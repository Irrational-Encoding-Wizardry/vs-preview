from itertools import count
from math import log1p
from functools import partial
from typing import List, Dict, Any

import numpy as np
import vapoursynth as vs
from vskernels import (Bicubic, Bilinear, Kernel, Lanczos, Robidoux, RobidouxSharp,
                       RobidouxSoft, Spline16, Spline36, Spline64)
from vsutil import get_w
from ..utils import get_prop
from ..core.types import VideoOutput

core = vs.core

common_scaler: Dict[str, List[Kernel]] = {
    "Bilinear": [
        Bilinear()
    ],
    "Bicubic": [
        Bicubic(1 / 3, 1 / 3),
        Bicubic(.5, 0),
        Bicubic(0, 0.5),
        Bicubic(1, 0),
        Bicubic(0, 1),
        Bicubic(0.2, 0.5),
        Bicubic(0.5, 0.5)
    ],
    "Robidoux": [
        Robidoux(),
        RobidouxSharp(),
        RobidouxSoft()
    ],
    "Lanczos": [
        Lanczos(2),
        Lanczos(3),
        Lanczos(4),
        Lanczos(5),
    ],
    "Spline": [
        Spline16(), Spline36(), Spline64()
    ]
}


def getnative_modifyframe(
    f: List[vs.VideoFrame], n: int, min_h: int, max_h: int, plot_width: int, plot_height: int, callback: Any
) -> vs.VideoFrame:
    resolutions: List[int] = []
    vals: List[float] = [
        get_prop(x.props, 'PlaneStatsAverage', float) for x in f[1:]
    ]

    ratios = [
        nextv and currv / nextv for currv, nextv in zip(vals, vals[1:] + vals[-1:])
    ]

    sorted_array = sorted(ratios, reverse=True)
    max_difference = sorted_array[0]

    i = 0

    while i < 5 and len(sorted_array):
        diff = sorted_array.pop(0)

        if diff - 1 > (max_difference - 1) * 0.33:
            current = ratios.index(diff)

            for res in resolutions:
                if res - 20 < current < res + 20:
                    break
            else:
                resolutions.append(current)

            i += 1

    callback([(r + min_h, vals[r]) for r in resolutions])

    fdst = f[0].copy()
    fdarr = np.asarray(fdst[0])

    sorted_vals = sorted(vals)

    nvals = len(vals)
    minval, maxval = sorted_vals[0] - (1e-7 * 2), sorted_vals[-1]

    scaled_max_val = log1p((maxval - minval) / (maxval - minval) * plot_height)

    scaled_vals = [
        log1p((x - minval) / (maxval - minval) * plot_height) / scaled_max_val * plot_height
        for x in vals
    ]

    interpolated = np.interp(np.arange(0, nvals, nvals / plot_width), np.arange(0, nvals), scaled_vals)

    for xc, ycurr, xn, ynext in zip(
        count(), interpolated, count(1), [interpolated[0], *interpolated[:-1]]
    ):
        yicurr = int(ycurr)
        yinext = int(ynext)

        diff = abs(yicurr - yinext)

        if diff:
            for i, y in enumerate(range(min(yicurr, yinext), max(yicurr, yinext)), 1):
                if diff >= 5 and ((i >= diff // 2) if yicurr - yinext > 0 else (i <= diff // 2)):
                    fdarr[int(plot_height - y - 1)][xn] = 255
                else:
                    fdarr[int(plot_height - y - 1)][xc] = 255
        else:
            fdarr[int(plot_height - yicurr - 1)][xc] = 255

    np.copyto(np.asarray(fdst[0]), fdarr)

    return fdst


def getnative_graph(
    output: VideoOutput,
    min_h: int = 900, max_h: int = 2000, steps: int = 1,
    plot_width: int = 1920, plot_height: int = 1080
) -> vs.VideoNode:
    from ..utils.utils import video_heuristics

    kernel = common_scaler['Bicubic'][0]

    is_rgb = output.source.clip.format.color_family == vs.RGB

    heuristics = video_heuristics(output.source.clip, output.props, not is_rgb)  # type: ignore

    if is_rgb:
        heuristics |= {'matrix_in_s': 'rgb', 'primaries_in_s': 'st428', 'transfer_in_s': 'srgb', 'range_in_s': 'full'}

    clip_y = output.source.clip.resize.Bicubic(format=vs.GRAYS, **heuristics)

    descaled_clips = [
        core.std.Expr([
            clip_y, kernel.scale(
                kernel.descale(
                    clip_y, get_w(h, not clip_y.width & 1), h
                ), clip_y.width, clip_y.height
            )
        ], 'x y - abs dup 0.015 > swap 0 ?')
        .std.CropRel(5, 5, 5, 5)
        .std.PlaneStats().resize.Point(1, 1, vs.GRAY8)
        for h in range(min_h, max_h + 1, steps)
    ]

    graphbk = clip_y.std.BlankClip(plot_width, plot_height, format=vs.GRAY8)

    graph = graphbk.std.ModifyFrame(
        [graphbk, *descaled_clips], partial(
            getnative_modifyframe, min_h=min_h, max_h=max_h,
            plot_width=plot_width, plot_height=plot_height,
            callback=lambda x: print(x)
        )
    )

    aa_graph = graph.std.Maximum().std.Maximum().std.Minimum()
    aa_graph = aa_graph.resize.Bicubic(plot_width * 2, plot_height * 2)
    aa_graph = aa_graph.std.Minimum().std.Deflate().std.Deflate()
    aa_graph = aa_graph.std.Expr('4 x *')
    graph_up = graph.resize.Bicubic(plot_width * 2, plot_height * 2)
    aa_graph = graph_up.std.BoxBlur().std.Merge(aa_graph)
    aa_graph = aa_graph.resize.Bicubic(plot_width, plot_height)

    return aa_graph.akarin.Expr("""x[-1,0] 158 = x 126 = and 0 x ?""")
