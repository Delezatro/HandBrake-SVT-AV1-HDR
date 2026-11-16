"""Windows smoke tests. Synthetic inputs cannot prove the reported ISO crash fixed."""
import argparse
import ctypes
from fractions import Fraction
import json
from pathlib import Path
import re
import subprocess
import sys
from manifest import digest


def run(command, log):
    result = subprocess.run([str(x) for x in command], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=600)
    log.write_bytes(result.stdout)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}; see {log}")
    return result.stdout.decode(errors="replace")


def check_dll(path):
    hb = ctypes.CDLL(str(path.resolve()))
    hb.hb_global_init_no_hardware.restype = ctypes.c_int
    assert hb.hb_global_init_no_hardware() == 0
    hb.hb_get_version.argtypes = [ctypes.c_void_p]
    hb.hb_get_version.restype = ctypes.c_char_p
    print("Packaged libhb:", hb.hb_get_version(None).decode())
    hb.hb_video_encoder_get_from_name.argtypes = [ctypes.c_char_p]
    hb.hb_video_encoder_get_from_name.restype = ctypes.c_int
    encoder = hb.hb_video_encoder_get_from_name(b"svt_av1_10bit")
    assert encoder != 0
    for function, expected in (("hb_video_encoder_get_tunes", {"grain"}),
                               ("hb_video_encoder_get_presets", {"-2", "-3"}),
                               ("hb_video_encoder_get_profiles", {"high"})):
        fn = getattr(hb, function)
        fn.argtypes = [ctypes.c_int]
        fn.restype = ctypes.POINTER(ctypes.c_char_p)
        values = fn(encoder)
        names = []
        for index in range(100):
            if not values[index]:
                break
            names.append(values[index].decode())
        assert expected.issubset(names), (function, names)
        print(function, names)
    hb.hb_global_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--publish", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dll-only", type=Path)
    args = parser.parse_args()
    if args.dll_only:
        check_dll(args.dll_only)
        return
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((args.native / "build-manifest.json").read_text())
    assert digest(args.publish / "hb.dll") == manifest["binaries"]["hb.dll"]
    assert (args.publish / "HandBrake.exe").is_file()
    assert (args.publish / "HandBrake.Worker.exe").is_file()
    run([sys.executable, __file__, "--dll-only", args.publish / "hb.dll"], args.output / "dll.log")
    cli = (args.native / "HandBrakeCLI.exe").resolve()
    run([cli, "--version"], args.output / "version.log")
    run(["ffmpeg", "-version"], args.output / "ffmpeg-version.log")
    run(["ffprobe", "-version"], args.output / "ffprobe-version.log")
    source = args.output / "source.mkv"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=size=128x128:rate=24",
         "-frames:v", "8", "-pix_fmt", "yuv444p10le", "-c:v", "ffv1", source], args.output / "generate.log")
    hdr_source = args.output / "source-hdr.mkv"
    run(["ffmpeg", "-y", "-i", source, "-frames:v", "8", "-c:v", "libx265", "-preset", "ultrafast",
         "-vf", "setparams=color_primaries=bt2020:color_trc=smpte2084:colorspace=bt2020nc",
         "-color_primaries", "bt2020", "-color_trc", "smpte2084", "-colorspace", "bt2020nc",
         "-x265-params", "pools=2:frame-threads=1:lossless=1:repeat-headers=1:colorprim=9:transfer=16:colormatrix=9:"
         "master-display=G(8500,39850)B(6550,2300)R(35400,14600)WP(15635,16450)L(10000000,50):"
         "max-cll=1000,400", hdr_source], args.output / "generate-hdr.log")
    cases = [
        ("420-8-grain", "svt_av1", "main", "8", "grain", "yuv420p", False),
        ("420-10", "svt_av1_10bit", "main", "8", "vq", "yuv420p10le", False),
        ("444-8", "svt_av1", "high", "8", "vq", "yuv444p", False),
        ("444-10-hdr", "svt_av1_10bit", "high", "8", "vq", "yuv444p10le", True),
        ("preset-minus2", "svt_av1_10bit", "main", "-2", "vq", "yuv420p10le", False),
        ("preset-minus3", "svt_av1_10bit", "main", "-3", "vq", "yuv420p10le", False),
    ]
    results = []
    for name, encoder, profile, preset, tune, pixel_format, hdr in cases:
        target = args.output / (name + ".mkv")
        options = "lp=2"
        log = run([cli, "-i", hdr_source if hdr else source, "-o", target, "-e", encoder, "--encoder-profile", profile,
                   "--encoder-preset", preset, "--encoder-tune", tune, "-q", "30", "-a", "none",
                   "--crop", "0:0:0:0", "--width", "128", "--height", "128", "--non-anamorphic",
                   "--previews", "1:0", "-x", options], args.output / (name + ".log"))
        assert "Encode done!" in log, name
        assert re.search(r"SVT-AV1.*4\.3", log), "Encoder version not confirmed in log"
        # libaom's FFmpeg wrapper does not expose HDR frame side data. Require
        # dav1d explicitly so a decoder change cannot silently weaken this test.
        probe = run(["ffprobe", "-v", "error", "-c:v", "libdav1d", "-select_streams", "v:0", "-show_streams",
                     "-show_frames", "-of", "json", target], args.output / (name + ".json"))
        data = json.loads(probe)
        video = data["streams"][0]
        assert video["codec_name"] == "av1" and video["pix_fmt"] == pixel_format, video
        assert video["profile"] == ("High" if profile == "high" else "Main"), video
        assert len(data["frames"]) == 8, "Unexpected encoded frame count"
        if hdr:
            assert video["color_transfer"] == "smpte2084" and video["color_primaries"] == "bt2020"
            assert video["color_space"] == "bt2020nc"
            metadata = {item["side_data_type"]: item for item in data["frames"][0].get("side_data_list", [])}
            light = metadata["Content light level metadata"]
            assert light["max_content"] == 1000 and light["max_average"] == 400
            mastering = metadata["Mastering display metadata"]
            assert Fraction(mastering["max_luminance"]) == 1000
            # AV1 MDCV quantizes minimum luminance in units of 1/16384 cd/m2.
            assert abs(Fraction(mastering["min_luminance"]) - Fraction(1, 200)) <= Fraction(1, 32768)
            for key, value in {"red_x": "0.708", "red_y": "0.292", "green_x": "0.170",
                               "green_y": "0.797", "blue_x": "0.131", "blue_y": "0.046",
                               "white_point_x": "0.3127", "white_point_y": "0.3290"}.items():
                assert abs(Fraction(mastering[key]) - Fraction(value)) <= Fraction(1, 131072)
        run(["ffmpeg", "-v", "error", "-xerror", "-c:v", "libdav1d", "-i", target, "-f", "null", "-"], args.output / (name + "-decode.log"))
        results.append({"case": name, "status": "passed"})
    (args.output / "results.json").write_text(json.dumps({
        "synthetic_tests": results,
        "original_bluray_iso": "NOT TESTED: requires the affected source and GUI reproduction",
        "gui_interactive_scan": "NOT TESTED: DLL API smoke test only",
        "hdr10plus_dolby_vision": "NOT TESTED: no representative dynamic metadata fixtures",
    }, indent=2))


if __name__ == "__main__":
    main()
