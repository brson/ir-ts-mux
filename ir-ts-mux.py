import argparse
import os
import wave
import shutil


def get_stereo_pair(files, base_name):
    left_file = f"{base_name} L.wav"
    right_file = f"{base_name} R.wav"
    return left_file if left_file in files else None, right_file if right_file in files else None


def read_wav(filename):
    with wave.open(filename, 'rb') as wav:
        params = wav.getparams()
        frames = wav.readframes(params.nframes)
    return params, frames


def write_wav(filename, params, frames):
    with wave.open(filename, 'wb') as wav:
        wav.setparams(params)
        wav.writeframes(frames)


def mux_files(indir, outdir):
    for root, _, files in os.walk(indir):
        rel_path = os.path.relpath(root, indir)
        out_path = os.path.join(outdir, rel_path)
        os.makedirs(out_path, exist_ok=True)
        
        processed = set()
        
        for file in files:
            if file.endswith(" L.wav") or file.endswith(" R.wav"):
                base_name = file[:-6]
                if base_name in processed:
                    continue
                left_file, right_file = get_stereo_pair(files, base_name)
                if left_file and right_file:
                    left_params, left_frames = read_wav(os.path.join(root, left_file))
                    right_params, right_frames = read_wav(os.path.join(root, right_file))
                    if left_params != right_params:
                        print(f"Skipping {base_name} due to mismatched parameters.")
                        continue
                    out_filename = os.path.join(out_path, f"{base_name}.wav")
                    quad_frames = b''.join([left_frames[i:i+2] + right_frames[i:i+2] for i in range(0, len(left_frames), 2)])
                    write_wav(out_filename, left_params._replace(nchannels=4), quad_frames)
                    processed.add(base_name)
                else:
                    shutil.copy2(os.path.join(root, file), os.path.join(out_path, file))
            else:
                shutil.copy2(os.path.join(root, file), os.path.join(out_path, file))


def demux_files(indir, outdir):
    for root, _, files in os.walk(indir):
        rel_path = os.path.relpath(root, indir)
        out_path = os.path.join(outdir, rel_path)
        os.makedirs(out_path, exist_ok=True)
        
        for file in files:
            if file.endswith(".wav"):
                in_filepath = os.path.join(root, file)
                with wave.open(in_filepath, 'rb') as wav:
                    params = wav.getparams()
                    if params.nchannels == 4:
                        frames = wav.readframes(params.nframes)
                        left_frames = b''.join([frames[i:i+2] for i in range(0, len(frames), 4)])
                        right_frames = b''.join([frames[i+2:i+4] for i in range(0, len(frames), 4)])
                        left_filename = os.path.join(out_path, f"{file[:-4]} L.wav")
                        right_filename = os.path.join(out_path, f"{file[:-4]} R.wav")
                        write_wav(left_filename, params._replace(nchannels=2), left_frames)
                        write_wav(right_filename, params._replace(nchannels=2), right_frames)
                    else:
                        shutil.copy2(in_filepath, os.path.join(out_path, file))


def main():
    parser = argparse.ArgumentParser(description="Convert true stereo impulse responses between split and quad formats.")
    parser.add_argument("--indir", required=True, help="Input directory")
    parser.add_argument("--outdir", required=True, help="Output directory")
    parser.add_argument("--demux", action="store_true", help="Split (demux) quad-channel files instead of merging")
    args = parser.parse_args()
    
    if args.demux:
        demux_files(args.indir, args.outdir)
    else:
        mux_files(args.indir, args.outdir)


if __name__ == "__main__":
    main()
