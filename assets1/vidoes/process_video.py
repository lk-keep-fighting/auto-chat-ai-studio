import os
import subprocess
import pandas as pd
import traceback
import textwrap
import math
import random
import PIL.Image

# ================= 修复 Pillow 报错补丁 =================
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
# ======================================================
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips

# ------- 配置区 (主脚本) -------
VIDEO_DIR = r"D:\videos\input"      # 原始视频文件夹
MUSIC_DIR = r"D:\videos\music"      # 背景音乐文件夹
OUTPUT_DIR = r"D:\videos\output"    # 输出主文件夹
EXCEL_FILE = r"D:\videos\clips.xlsx"

# ❗❗ 字体路径
FONT_PATH = "C:/Windows/Fonts/impact.ttf"

# ffmpeg 路径
FFMPEG_CMD = "ffmpeg"
FFPROBE_CMD = "ffprobe"

# 编码参数
VIDEO_CODEC = "libx264"
VIDEO_PRESET = "fast"
VIDEO_CRF = "22"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"
# ----------------------

# ------- 配置区 (脚本 B - 视频处理) -------
FOLDER_A = r"D:\videos\片尾素材" 
FOLDER_B = r"D:\videos\画中画素材"

# 图片路径 (已设为 D:\videos\素材)
ARROW_IMAGE = r"D:\videos\素材\arrow.png"
TEXT_IMAGE = r"D:\videos\素材\text.png"

# --- 尺寸与位置设置 ---
ARROW_SIZE = (130, 130)
TEXT_SIZE_WIDTH = 350
POSITION_Y = 0.35
ARROW_POS_X = 0.95
TEXT_POS_X = 0.82

# --- 动画设置 ---
BOUNCE_SPEED = 6.0
BOUNCE_HEIGHT = 20

# --- 强制压缩设置 ---
ENABLE_RESIZE = True       
TARGET_WIDTH = 1080        
# ----------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)
TEMP_CLIPS_DIR = os.path.join(OUTPUT_DIR, "temp_clips")
os.makedirs(TEMP_CLIPS_DIR, exist_ok=True)

# -----------------------------------------------------------------------
# 🛠️ 自动生成临时素材函数
# -----------------------------------------------------------------------
def ensure_image_exists(path, default_name, color, size=(200, 200)):
    if os.path.exists(path): return path
    print(f"    ⚠️ 警告: 找不到图片 {path}，使用临时色块代替...")
    temp_img_path = os.path.join(TEMP_CLIPS_DIR, default_name)
    if not os.path.exists(temp_img_path):
        img = PIL.Image.new('RGBA', size, color)
        img.save(temp_img_path)
    return temp_img_path

# -----------------------------------------------------------------------
# FFmpeg 工具函数
# -----------------------------------------------------------------------
def run(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8')
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"    ⚠️ FFmpeg 出错: {process.returncode}")
    return process.returncode, stdout, stderr

def get_media_info(path, info_type='duration'):
    if info_type == 'duration':
        cmd_part = ["-show_entries", "format=duration"]
    else:
        cmd_part = ["-select_streams", "v:0", "-show_entries", "stream=r_frame_rate"]
    cmd = [ FFPROBE_CMD, "-v", "error", *cmd_part, "-of", "default=noprint_wrappers=1:nokey=1", path ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        if "/" in out:
            num, den = out.split("/")
            return float(num) / float(den)
        return float(out)
    except Exception:
        return 30.0 if info_type == 'fps' else 0

def parse_time(t, fps=30.0):
    if pd.isna(t): return None
    t = str(t).strip()
    if not t: return None
    try:
        parts = [float(p) for p in t.split(":") if p]
        if len(parts) == 4: return parts[0]*3600 + parts[1]*60 + parts[2] + parts[3]/fps
        if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
        if len(parts) == 2: return parts[0]*60 + parts[1]
        if len(parts) == 1: return parts[0]
    except ValueError:
        return None
    return None

def generate_cover_image(video_path, time_pos, title, subtitle, output_path):
    if not os.path.exists(FONT_PATH):
        print(f"    ❌ 字体不存在: {FONT_PATH}")
        return False
    font_path_clean = FONT_PATH.replace("\\", "/").replace(":", "\\:")
    raw_title = str(title).strip().replace("'", "’") if pd.notna(title) else ""
    raw_subtitle = str(subtitle).strip().replace("'", "’") if pd.notna(subtitle) else ""
    
    title_lines = textwrap.wrap(raw_title.upper(), width=10) 
    subtitle_lines = textwrap.wrap(raw_subtitle.upper(), width=15) if raw_subtitle else []

    all_lines_to_draw = []
    for line in title_lines:
        all_lines_to_draw.append({'text': line, 'color': 'yellow', 'size': 170})
    for line in subtitle_lines:
        all_lines_to_draw.append({'text': line, 'color': 'white', 'size': 120})

    if not all_lines_to_draw: return False

    line_height = 200 
    total_block_height = len(all_lines_to_draw) * line_height
    filters = []
    
    for i, item in enumerate(all_lines_to_draw):
        vertical_shift = 200
        y_offset_expression = f"(h-{total_block_height})/2 + {i * line_height} + {vertical_shift}"
        safe_text = item['text'].replace(":", "\\:") 
        draw_cmd = (
            f"drawtext=fontfile='{font_path_clean}':text='{safe_text}':fontcolor={item['color']}:"
            f"fontsize={item['size']}:x=(w-text_w)/2:y={y_offset_expression}:"
            f"borderw=8:bordercolor=black:shadowx=6:shadowy=6:box=1:boxcolor=black@0.65:boxborderw=25"
        )
        filters.append(draw_cmd)

    cmd = [FFMPEG_CMD, "-y", "-ss", str(time_pos), "-i", video_path, "-vf", ",".join(filters), 
           "-vframes", "1", "-q:v", "2", output_path]
    rc, _, _ = run(cmd)
    return rc == 0

# -----------------------------------------------------------------------
# 脚本 B 的函数 
# -----------------------------------------------------------------------
def get_random_video(folder_path):
    if not os.path.exists(folder_path): return None
    files = [f for f in os.listdir(folder_path) if f.endswith(('.mp4', '.mov', '.MP4', '.MOV'))]
    if not files: return None
    return os.path.join(folder_path, random.choice(files))

def process_videos(input_video_path, output_video_path): 
    """处理单个视频，添加箭头、文案、画中画、片尾"""
    main_clip = None
    processed_main_clip = None
    final_video = None
    outro_clip = None
    
    try:
        real_arrow_path = ensure_image_exists(ARROW_IMAGE, "temp_arrow.png", (255, 0, 0, 255), size=ARROW_SIZE)
        real_text_path = ensure_image_exists(TEXT_IMAGE, "temp_text.png", (0, 0, 255, 255), size=(TEXT_SIZE_WIDTH, 100))

        main_clip = VideoFileClip(input_video_path)
        if ENABLE_RESIZE and main_clip.w > TARGET_WIDTH:
            main_clip = main_clip.resize(width=TARGET_WIDTH)

        w, h = main_clip.size
        layers = [main_clip]

        # [功能 A] 画中画
        PIP_START_TIME = 30
        if main_clip.duration > PIP_START_TIME:
            pip_path = get_random_video(FOLDER_B)
            if pip_path:
                print(f"     > 添加画中画: {os.path.basename(pip_path)}")
                pip_clip = VideoFileClip(pip_path)
                pip_clip = pip_clip.without_audio().resize(width=w).set_position(('center', 0))
                remaining_time = main_clip.duration - PIP_START_TIME
                if pip_clip.duration > remaining_time:
                     pip_clip = pip_clip.subclip(0, remaining_time)
                pip_clip = pip_clip.set_start(PIP_START_TIME)
                layers.append(pip_clip)

        # [功能 B] 箭头和文案
        arrow_center_x = w * ARROW_POS_X
        text_center_x = w * TEXT_POS_X
        base_arrow_y = h * POSITION_Y

        def bounce_pos(t):
            return (arrow_center_x - ARROW_SIZE[0]/2, base_arrow_y + math.sin(BOUNCE_SPEED * t) * BOUNCE_HEIGHT)

        arrow_clip = (ImageClip(real_arrow_path).resize(ARROW_SIZE).set_duration(main_clip.duration).set_position(bounce_pos))
        txt_img = (ImageClip(real_text_path).resize(width=TEXT_SIZE_WIDTH).set_duration(main_clip.duration))
        
        txt_x = text_center_x - (txt_img.w / 2)
        txt_y = base_arrow_y - txt_img.h - 10
        txt_img = txt_img.set_pos((txt_x, txt_y))

        layers.append(txt_img)
        layers.append(arrow_clip)

        processed_main_clip = CompositeVideoClip(layers)

        # [功能 C] 拼接片尾
        outro_path = get_random_video(FOLDER_A)
        if outro_path:
            outro_clip = VideoFileClip(outro_path)
            if outro_clip.size != main_clip.size: outro_clip = outro_clip.resize(newsize=(w, h))
            if outro_clip.fps != main_clip.fps: outro_clip = outro_clip.set_fps(main_clip.fps)
            final_video = concatenate_videoclips([processed_main_clip, outro_clip], method="chain")
        else:
            final_video = processed_main_clip

        final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", fps=main_clip.fps, preset='ultrafast', threads=8, logger=None)
        
    except Exception as e:
        print(f"❌  process_videos 出错: {e}")
        traceback.print_exc()
    finally:
        if main_clip: main_clip.close()
        if final_video and final_video != processed_main_clip: final_video.close()
        if processed_main_clip: processed_main_clip.close()
        if outro_clip: outro_clip.close()

# ===== 主流程 =====
try:
    print(f"--- 正在读取 Excel 文件: {EXCEL_FILE} ---")
    df = pd.read_excel(EXCEL_FILE)
    df.columns = df.columns.str.strip().str.lower()

    required_columns = ['filename', 'start', 'end', 'folder2', 'folder3']
    if any(col not in df.columns for col in required_columns):
        raise ValueError(f"Excel 缺少列: {required_columns}")

    if 'time' in df.columns and 'cover_time' not in df.columns: df.rename(columns={'time': 'cover_time'}, inplace=True)
    for col in ['music', 'cover_time', 'title', 'subtitle']:
        if col not in df.columns: df[col] = '' if col != 'cover_time' else None

    df['filename'] = df['filename'].fillna(method='ffill')
    df['filename'] = df['filename'].astype(str).str.strip()
    df['folder2'] = df['folder2'].fillna('').astype(str).str.strip()
    df['folder3'] = df['folder3'].fillna('').astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    df['music'] = df['music'].fillna('').astype(str).str.strip()

    video_info_cache = {}
    
    # 第一次分组：按文件名（比如 A.mp4）
    grouped = df.groupby('filename')

    for vid_filename, group in grouped:
        file_stem = os.path.splitext(vid_filename)[0]
        target_output_dir = os.path.join(OUTPUT_DIR, file_stem)
        os.makedirs(target_output_dir, exist_ok=True)

        print(f"\n=================================================")
        print(f"📂 正在处理源视频: {vid_filename}")
        
        # ❗❗❗ 关键修改：在这里就进行第二次分组（按 Folder2 和 Folder3）
        # 确保每次循环只处理属于这一个“小视频”的片段
        for (f2_name, f3_name), sub_group in group.groupby(['folder2', 'folder3']):
            
            # --- 1. 剪辑当前小视频的片段 ---
            clips_for_this_folder = []
            
            for index, row in sub_group.iterrows():
                video_full_name = row['filename']
                input_path = os.path.join(VIDEO_DIR, video_full_name)
                
                if not os.path.isfile(input_path): continue

                if input_path not in video_info_cache:
                    video_info_cache[input_path] = {'fps': get_media_info(input_path, 'fps')}
                current_fps = video_info_cache[input_path]['fps']

                # 封面生成（逻辑不变）
                cover_t_str = row.get('cover_time')
                if pd.notna(cover_t_str) and str(cover_t_str).strip() != "":
                    cover_time_sec = parse_time(cover_t_str, fps=current_fps)
                    if cover_time_sec is not None:
                        cover_out = os.path.join(target_output_dir, f"{f2_name}{f3_name}_cover.jpg")
                        print(f"  🖼️ 生成封面: {row.get('title', '')}")
                        if generate_cover_image(input_path, cover_time_sec, row.get('title', ''), row.get('subtitle', ''), cover_out):
                            print(f"    ✅ 封面完成")

                # 计算起止时间
                start = parse_time(row["start"], fps=current_fps)
                end = parse_time(row["end"], fps=current_fps)
                if start is None or end is None: continue

                # 剪切
                temp_name = f"{file_stem}_{f2_name}{f3_name}_{index}.mp4"
                out_clip_path = os.path.join(TEMP_CLIPS_DIR, temp_name)
                
                cmd = [FFMPEG_CMD, "-y", "-i", input_path, "-ss", str(start), "-to", str(end),
                       "-c:v", VIDEO_CODEC, "-preset", VIDEO_PRESET, "-crf", VIDEO_CRF,
                       "-c:a", AUDIO_CODEC, "-b:a", AUDIO_BITRATE, "-avoid_negative_ts", "1", out_clip_path]
                
                rc, _, _ = run(cmd)
                if rc == 0: clips_for_this_folder.append(out_clip_path)

            # --- 2. 合并片段 ---
            if clips_for_this_folder:
                # 给临时合并文件起个独特名字，防止混淆
                list_path = os.path.join(TEMP_CLIPS_DIR, f"list_{file_stem}_{f2_name}_{f3_name}.txt")
                with open(list_path, "w", encoding="utf-8") as f:
                    for p in clips_for_this_folder:
                        # 转换路径格式并转义单引号
                        escaped_path = p.replace('\\', '/').replace("'", "'\\''")
                        f.write(f"file '{escaped_path}'\n")

                merged_temp = os.path.join(TEMP_CLIPS_DIR, f"merged_{file_stem}_{f2_name}_{f3_name}.mp4")
                run([FFMPEG_CMD, "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", merged_temp])

                # --- 3. 施加特效（脚本B逻辑） ---
                final_video_path = os.path.join(target_output_dir, f"{f2_name}{f3_name}.mp4")
                print(f"  ✨ 正在生成最终视频: {f2_name}{f3_name}.mp4 ...")
                
                # 传入的是刚刚合并好的“小片段”，而不是巨大的源视频
                process_videos(merged_temp, final_video_path)

    print("\n🎉 全部处理结束")

except Exception:
    traceback.print_exc()
finally:
    input("按 Enter 退出...")