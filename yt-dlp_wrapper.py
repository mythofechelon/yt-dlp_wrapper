"""
Version history:
	• v2.7.0:
		- Date: 2026/04/26
		- Changes:
			= Added numbers to processing message so you can see overall progress.
	• v2.6.0:
		- Date: 2026/03/13
		- Changes:
			= Refactored to work for anyone.
	• v2.5.2:
		- Date: 2026/02/24
		- Changes:
			= Fixed error "'WindowsPath' object has no attribute 'exist'" when trying to replace the existing yt-dlp.exe file.
	• v2.5.1:
		- Date: 2025/12/13
		- Changes:
			= Fixed error when trying to create the old EXE file and it already exists.
	• v2.5.0:
		- Date: 2025/11/27
		- Changes:
			= Added stripping of Unicode characters from the generated file name so that the existance check works as expected, as yt-dlp seems to strip Unicode characters from its console output.
			= Adjusted default folder handling so that the last-used one is suggested for the next one.
	• v2.4.0:
		- Date: 2025/11/18
		- Changes:
			= Added outputting of the file names.
			= Added a default target folder.
	• v2.3.0:
		- Date: 2025/11/18
		- Changes:
			= Added option to suppress full yt-dlp output.
			= Improved output.
			= Moved critical path checking out of the while loop so it's only done once when the script is initially run.
	• v2.2.0:
		- Date: 2025/11/17
		- Changes: Split out binary updating to dedicated function and run first.
	• v2.1.0:
		- Date: 2025/11/16
		- Changes: Added output status report.
	• v2.0.0:
		- Date: 2025/11/14
		- Changes: Added updater for yt-dlp.exe.
	• v1.0.0:
		- Date: 2025/11/02
		- Changes: Created.
"""



import os
import subprocess
from pathlib import Path
import requests


YTDLP_ENV_KEY = "YT-DLP_PATH"

FFMPEG_ENV_KEY = "FFMPEG_PATH"

WRAPPING_CHARS = "'\" "

SEPARATOR_LIST = "\n• "

SEPARATOR_MAIN_SECTION = "\n" + "─" * 75

SEPARATOR_SUB_SECTION = "\n" + "─" * 15

DEFAULT_TARGET_FOLDER_PATH = Path(os.getenv("userProfile")) / "Downloads"



def get_file_version(file_path):
	import win32api # "pip install pywin32"
	
	file_info = win32api.GetFileVersionInfo(str(file_path), "\\")
	
	file_version_section_1 = str(win32api.HIWORD(file_info["FileVersionMS"]))
	
	file_version_section_2 = str(win32api.LOWORD(file_info["FileVersionMS"]))
	
	file_version_section_3 = str(win32api.HIWORD(file_info["FileVersionLS"]))
	
	file_version_section_4 = str(win32api.LOWORD(file_info["FileVersionLS"]))
	
	file_version_section_list = [
		file_version_section_1,
		file_version_section_2,
		file_version_section_3,
		file_version_section_4,
	]
	
	return file_version_section_list

def update_exe_file(exe_release_url, exe_file_path):
	exe_current_file_version_list = get_file_version(exe_file_path)
	
	del exe_current_file_version_list[-1] # 4th version section is unused with yt-dlp.
	
	for date_index, date_value in enumerate(exe_current_file_version_list):
		if len(date_value) == 1:
			exe_current_file_version_list[date_index] = f"0{date_value}" # To (1) be in the same format as the release tags and (2) allow for using maths operators on dates converted to integers later.
	
	exe_current_file_version_string = ".".join(exe_current_file_version_list)
	
	exe_current_file_version_int = int("".join(exe_current_file_version_list))
	
	
	
	exe_latest_release_api_response = requests.get(exe_release_url)
	
	exe_latest_release_api_response.raise_for_status()
	
	exe_latest = exe_latest_release_api_response.json()
	
	exe_latest_release_version_string = exe_latest["tag_name"]
	
	exe_latest_release_version_int = int(exe_latest_release_version_string.replace(".", ""))
	
	
	
	if exe_latest_release_version_int <= exe_current_file_version_int:
		pass
		
	else:
		print(f"\nNew version of '{exe_file_path.name}' available: {exe_current_file_version_string} ↗ {exe_latest_release_version_string}. Updating will likely prevent errors.")
		
		exe_update = input("Update? (y/n)\n")
		
		if exe_update.lower().startswith("y"):
			for exe_latest_release_file in exe_latest["assets"]:
				if exe_latest_release_file["name"].lower() == "yt-dlp.exe":
					exe_latest_release_file_url = exe_latest_release_file["browser_download_url"]
					
					try:
						with requests.get(exe_latest_release_file_url, stream=True) as exe_latest_file_api_response:
							exe_latest_file_api_response.raise_for_status()
							
							exe_latest_file_name_with_version = f"yt-dlp-{exe_latest_release_version_string}.exe"
							
							exe_latest_file_with_version_path = exe_file_path.with_name(exe_latest_file_name_with_version)
							
							with open(exe_latest_file_with_version_path, "wb") as exe_latest_file:
								for chunk in exe_latest_file_api_response.iter_content(chunk_size=8192):
									exe_latest_file.write(chunk)
									
							print(f"\nDownloaded {exe_latest_release_file_url} to '{exe_latest_file_with_version_path}'.")
						
						exe_current_file = exe_file_path.name
						
						exe_old_file_name = f"yt-dlp-{exe_current_file_version_string}.exe"
						
						exe_old_file_with_version_path = exe_file_path.with_name(exe_old_file_name)
						
						if exe_old_file_with_version_path.exists():
							exe_old_file_with_version_path.unlink() # Delete
						
						exe_file_path.rename(exe_old_file_with_version_path)
						
						print(f"\nRenamed '{exe_current_file}' to '{exe_old_file_name}'.")
						
						exe_file_path.write_bytes(exe_latest_file_with_version_path.read_bytes())
						
						print(f"\nDuplicated '{exe_latest_file_name_with_version}' as '{exe_current_file}'.")
						
					except Exception as error:
						print(f"\n{str(error)}")
					
					break
		
		print(SEPARATOR_SUB_SECTION)
	
	return

def validate_and_save_file_path(message, env_key):
	while True:
		try:
			file_path = Path(input(message).strip(WRAPPING_CHARS))
			
			if file_path.exists() and file_path.is_file() and file_path.suffix.lower() == ".exe":
				break
				
			else:
				raise ValueError("Invalid file path.")
				
		except Exception as error:
			print(f"[ERROR] {str(error)}")
	
	print(f"Setting environment variable '{env_key}'...")
	
	subprocess.run(["setx", env_key, file_path])
	
	return file_path

def main():
	ytdlp_file_path = os.getenv(YTDLP_ENV_KEY)
	
	if ytdlp_file_path:
		ytdlp_file_path = Path(ytdlp_file_path)
		
	else:
		ytdlp_file_path = validate_and_save_file_path(message="\nEnter the path to the yt-dlp .EXE file: ", env_key=YTDLP_ENV_KEY)
		
		print(SEPARATOR_SUB_SECTION)
		
		
		
	update_exe_file(
		exe_release_url="https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest",
		exe_file_path=ytdlp_file_path
	)
	
	
	
	ffmpeg_file_path = os.getenv(FFMPEG_ENV_KEY)
	
	if ffmpeg_file_path:
		ffmpeg_file_path = Path(ffmpeg_file_path)
		
	else:
		ffmpeg_file_path = validate_and_save_file_path(message="\nEnter the path to the FFMPEG .EXE file: ", env_key=FFMPEG_ENV_KEY)
		
		print(SEPARATOR_SUB_SECTION)
	
	
	
	last_target_folder_path = DEFAULT_TARGET_FOLDER_PATH
	
	while True:		
		target_folder_path = input(f"\nEnter the target folder path (default '{last_target_folder_path}'):\n").strip(WRAPPING_CHARS)
		
		if target_folder_path:
			last_target_folder_path = target_folder_path
			
		else:
			target_folder_path = last_target_folder_path
		
		if target_folder_path and Path(target_folder_path).exists() and Path(target_folder_path).is_dir():
			target_folder_path = Path(target_folder_path)
			
		else:
			print("\n[ERROR] Invalid folder path.")
			
			print(SEPARATOR_SUB_SECTION)
			
			continue
			
		print(SEPARATOR_SUB_SECTION)

		print("\nEnter the video URLs to download, one per line, followed by a blank line:")

		urls_all = []
		urls_succeeded = []
		urls_failed = []

		while True:
			line = input().strip()
			
			if not line:
				break
				
			urls_all.append(line)
			
		print(SEPARATOR_SUB_SECTION)
		
		ytdlp_print_full_output = input("\nPrint the full yt-dlp output? yes (default) / no\n")
		
		if not ytdlp_print_full_output or ytdlp_print_full_output.lower().startswith("y"):
			ytdlp_print_full_output = True
			
		else:
			ytdlp_print_full_output = False
			
		urls_all_count = len(urls_all)
		
		for video_index, video_url in enumerate(urls_all, start=1):
			try:
				print(SEPARATOR_SUB_SECTION)
				
				print(f"\nProcessing {video_url} ({video_index} of {urls_all_count}) ...\n")
				
				ytdlp_args = [
					"--paths", target_folder_path,
					"--replace-in-metadata", "title", r"[^0-9A-Za-z ._-]", "_",
					"--print", "after_move:%(filepath)s",
					"--no-quiet", "--progress",
					"--ffmpeg-location", ffmpeg_file_path,
					video_url
				]
				
				output_lines = []
				
				with subprocess.Popen([ytdlp_file_path, *ytdlp_args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1) as ytdlp_process:
					for output_line in ytdlp_process.stdout:
						if ytdlp_print_full_output:
							print(output_line, end="")
						
						output_lines.append(output_line)
						
				ytdlp_process.wait()
				
				output_lines_last_path = Path(output_lines[-1].strip())

				if ytdlp_process.returncode != 0:
					raise RuntimeError()
					
				elif "please report this issue" in "".join(output_lines).lower():
					raise Exception("Unexpected yt-dlp error.")
					
				elif not output_lines_last_path.exists() or not output_lines_last_path.is_file():
					raise Exception("Output file doesn't exist.")
					
				else:
					video_file_name = f"'{output_lines_last_path.name}'"
					
					print(f"\n[Success]. Saved to file: {video_file_name}")
					
					urls_succeeded.append(f"{video_url} → {video_file_name}")
			
			except Exception as error:
				print(f"\n [ERROR] {str(error)}")
				
				urls_failed.append(video_url)
			
				pass # No exceptions that can be handled.
			
		print(SEPARATOR_SUB_SECTION)
		
		print("\nResults:")
		
		if urls_failed:
			print(f"\n{len(urls_failed)}/{len(urls_all)} failed:{SEPARATOR_LIST}{SEPARATOR_LIST.join(urls_failed)}")
		
		if urls_succeeded:
			print(f"\n{len(urls_succeeded)}/{len(urls_all)} succeeded:{SEPARATOR_LIST}{SEPARATOR_LIST.join(urls_succeeded)}")
		
		print(SEPARATOR_MAIN_SECTION)
		
		
		
if __name__ == "__main__":
	main()