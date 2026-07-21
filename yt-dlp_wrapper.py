"""
Version history:
	• v2.9.0:
		- Date: 2026/07/21
		- Changes:
			= Added prefixing of current and total video numbers when full output is chosen.
	• v2.8.0:
		- Date: 2026/07/13
		- Changes:
			= Added support for Deno.
			= Added support for Unicode.
			= Added YouTube-specific output file name template of "<channel name> (<upload date as yyyy⧸mm⧸dd>)꞉ “<title>”". Unicode characters are used as per https://mythofechelon.co.uk/blog/2020/3/6/how-to-work-around-windows-restricted-characters
	• v2.7.1:
		- Date: 2026/06/24
		- Changes:
			= Changed EXE update function so errors are caught, printed, and suppressed.
			= Split validate_and_save_file_path() into get_valid_exe_path() and save_path().
			= Added validation of EXE paths retrieved from environment variables.
			= Changed handling of default target folder path so it's only changed if it's validated.
			= Improved logging to be more specific and standardised.
			= Added download links for yt-dlp and FFMPEG to ease the first-time set up.
			= Renamed update_exe_file() to check_and_update_exe_file() to be clearer.
			= Added improvement opportunities section to metadata.
			= Reverse order of .EXE checks so that the dependencies (only FFMPEG for now) are checked first.
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
		
Improvement opportunities:
	• None known.
"""



import os
import subprocess
from pathlib import Path
import requests
import re
import io
import shutil
import zipfile



DENO_ENV_KEY = "DENO_PATH"

FFMPEG_ENV_KEY = "FFMPEG_PATH"

YTDLP_ENV_KEY = "YT-DLP_PATH"

WRAPPING_CHARS = "'\" "

SEPARATOR_LIST = "\n• "

SEPARATOR_MAIN_SECTION = "\n" + "─" * 75

SEPARATOR_SUB_SECTION = "\n" + "─" * 15

DEFAULT_TARGET_FOLDER_PATH = Path(os.getenv("userProfile")) / "Downloads"

PRINT_FORMAT_ERROR = "[ERROR] {message}"

PRINT_FORMAT_SUCCESS = "[Success] {message}"



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

def check_and_update_exe_file(exe_release_url, exe_file_path):
	exe_file_name_with_extension = exe_file_path.name
	
	exe_file_name_without_extension = exe_file_path.stem
	
	print(f"\nChecking version of \"{exe_file_name_with_extension}\" against {exe_release_url} ...")
		
	exe_current_file_version_list = get_file_version(exe_file_path)
	
	del exe_current_file_version_list[-1] # 4th version section is unused with yt-dlp and Deno.
	
	if re.search(r"^20\d{2}$", exe_current_file_version_list[0]) and re.search(r"^0?[1-9]|1[012]$", exe_current_file_version_list[1]) and re.search(r"^0?[1-9]|[12][0-9]|3[01]$", exe_current_file_version_list[2]): # Date-based version.
		for index, value in enumerate(exe_current_file_version_list):
			if len(value) == 1:
				exe_current_file_version_list[index] = f"0{value}" # To (1) be in the same format as the release tags and (2) allow for using maths operators on dates converted to integers later.
	
	exe_current_file_version_string = ".".join(exe_current_file_version_list)
		
	print(f"\tCurrent: {exe_current_file_version_string}")
	
	exe_current_file_version_int = int("".join(exe_current_file_version_list))
	
	
	
	try:
		latest_release_api_response = requests.get(exe_release_url)
		
		latest_release_api_response.raise_for_status()
		
		latest_release = latest_release_api_response.json()
		
		latest_release_version_string = latest_release["tag_name"].strip("v")
		
		print(f"\tLatest:  {latest_release_version_string}")
		
		latest_release_version_int = int(latest_release_version_string.replace(".", ""))
		
		
		
		if latest_release_version_int <= exe_current_file_version_int:
			print("\nNo update available.")
			
		else:
			exe_update = input("\nNew version available. Update? (y/n)\n")
			
			if exe_update.lower().startswith("y"):
				for latest_release_file in latest_release["assets"]:
					if latest_release_file["name"].lower() == "yt-dlp.exe" or latest_release_file["name"].lower() == "deno-x86_64-pc-windows-msvc.zip":
						latest_release_file_url = latest_release_file["browser_download_url"]
						
						try:
							print(f"\nDownloading {latest_release_file_url} ...")
							
							latest_file_api_response = requests.get(latest_release_file_url, stream=True)
							
							latest_file_api_response.raise_for_status()
							
							buffer = io.BytesIO()

							for chunk in latest_file_api_response.iter_content(chunk_size=1024 * 1024):
								if chunk:
									buffer.write(chunk)
							
							latest_file_name_with_version = f"{exe_file_name_without_extension}-{latest_release_version_string}.exe"
								
							latest_file_path_with_version = exe_file_path.with_name(latest_file_name_with_version)

							buffer.seek(0)
							
							is_file_file = zipfile.is_zipfile(buffer)

							buffer.seek(0)
							
							if not is_file_file:
								with open(latest_file_path_with_version, "wb") as exe_file:
									shutil.copyfileobj(buffer, exe_file)
									
							else:
								with zipfile.ZipFile(buffer) as zip_file:
									for member in zip_file.infolist():
										if not member.is_dir() and member.filename.lower().endswith(".exe"):
											with zip_file.open(member) as source_exe_file, open(latest_file_path_with_version, "wb") as target_exe_file:
												shutil.copyfileobj(source_exe_file, target_exe_file)
							
							print(PRINT_FORMAT_SUCCESS.format(message=f"Saved to \"{latest_file_path_with_version}\"."))
							
							exe_current_file = exe_file_path.name
							
							exe_old_file_name = f"{exe_file_name_without_extension}-{exe_current_file_version_string}.exe"
							
							exe_old_file_with_version_path = exe_file_path.with_name(exe_old_file_name)
							
							if exe_old_file_with_version_path.exists():
								exe_old_file_with_version_path.unlink() # Delete
							
							exe_file_path.rename(exe_old_file_with_version_path)
							
							print(f"\nArchived old by renaming \"{exe_current_file}\" to \"{exe_old_file_name}\".")
							
							exe_file_path.write_bytes(latest_file_path_with_version.read_bytes())
							
							print(f"\nInstated new by duplicating \"{latest_file_name_with_version}\" as \"{exe_current_file}\".")
							
						except Exception as error:
							print("\n" + PRINT_FORMAT_ERROR.format(message=str(error)))
						
						break
	
	except Exception as error:
		print("\n" + PRINT_FORMAT_ERROR.format(message=str(error)))
	
	return

def save_path(validated_path, env_key):
	print(f"\nRemembering this for next time by setting environment variable \"{env_key}\" ...")
	
	subprocess.run(["setx", env_key, validated_path])

def get_valid_exe_path(name, setup_message, env_key=None):
	while True:
		try:
			file_path = None
			
			file_path_from_env = False
			
			if env_key:
				file_path = os.getenv(env_key)
				
				if file_path:
					print(f"\n{name} .EXE file path retrieved from environment variable \"{env_key}\":\n\"{file_path}\"")
					
					file_path_from_env = True
					
				else:
					print(f"\n{name} .EXE file path could not be retrieved from environment variable \"{env_key}\".")
			
			if not file_path:
				file_path = get_user_input(
					message=setup_message,
					blanks_allowed=False
				)
				
			print(f"\nChecking file path ...")
			
			file_path = Path(str(file_path).strip(WRAPPING_CHARS))
			
			if file_path.exists() and file_path.is_file() and file_path.suffix.lower() == ".exe":
				print(PRINT_FORMAT_SUCCESS.format(message="File path valid."))
				
				if not file_path_from_env:
					save_path(
						validated_path=file_path,
						env_key=env_key
					)
				
				return file_path
				
			else:
				raise ValueError("Invalid file path.")
			
		except Exception as error:
			print(PRINT_FORMAT_ERROR.format(message=str(error)))
	
def get_user_input(message, blanks_allowed=False):
	while True:
		user_input = input(message).strip(WRAPPING_CHARS)
		
		if not user_input and blanks_allowed == False:
			print("\n" + PRINT_FORMAT_ERROR.format(message="Empty input not allowed."))
			
		else:
			return user_input
	
	

def main():
	deno_file_path = get_valid_exe_path(
		name="Deno",
		setup_message="\nEnter the path to the Deno .EXE file (download from https://github.com/denoland/deno/releases/latest → \"deno-x86_64-pc-windows-msvc.zip\"), used to \"solve JavaScript challenges presented by YouTube\":\n",
		env_key=DENO_ENV_KEY
	)
	
	check_and_update_exe_file(
		exe_release_url="https://api.github.com/repos/denoland/deno/releases/latest",
		exe_file_path=deno_file_path
	)
			
	print(SEPARATOR_MAIN_SECTION)
	
	
	
	ffmpeg_file_path = get_valid_exe_path(
		name="FFMPEG",
		setup_message="\nEnter the path to the FFMPEG .EXE file (download from https://ffmpeg.org/download.html#build-windows), used to fix any issues with the created video files:\n",
		env_key=FFMPEG_ENV_KEY
	)
	
	print(SEPARATOR_MAIN_SECTION)
	
	
	
	ytdlp_file_path = get_valid_exe_path(
		name="yt-dlp",
		setup_message="\nEnter the path to the yt-dlp .EXE file (download from https://github.com/yt-dlp/yt-dlp/releases):\n",
		env_key=YTDLP_ENV_KEY
	)
	
	check_and_update_exe_file(
		exe_release_url="https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest",
		exe_file_path=ytdlp_file_path
	)
			
	print(SEPARATOR_MAIN_SECTION)
	
	
	
	last_target_folder_path = DEFAULT_TARGET_FOLDER_PATH
	
	while True:		
		target_folder_path = input(f"\nEnter the target folder path (default \"{last_target_folder_path}\"):\n").strip(WRAPPING_CHARS)
		
		if not target_folder_path:
			target_folder_path = last_target_folder_path
		
		print(f"\nChecking given path ...")
		
		if target_folder_path and Path(target_folder_path).exists() and Path(target_folder_path).is_dir():
			print(PRINT_FORMAT_SUCCESS.format(message="Folder path valid."))
			
			last_target_folder_path = target_folder_path
			
			target_folder_path = Path(target_folder_path)
			
		else:
			print(PRINT_FORMAT_ERROR.format(message="Folder path invalid."))
			
			print(SEPARATOR_SUB_SECTION)
			
			continue
			
		print(SEPARATOR_MAIN_SECTION)
		
		

		print("\nEnter the video URLs to download, one per line, followed by a blank line:")

		urls_all = []
		urls_succeeded = []
		urls_failed = []

		while True:
			line = input().strip()
			
			if not line:
				break
				
			urls_all.append(line)
			
		print(SEPARATOR_MAIN_SECTION)
		
		
		
		ytdlp_print_full_output = input("\nPrint the full yt-dlp output? yes (default) / no\n")
		
		if not ytdlp_print_full_output or ytdlp_print_full_output.lower().startswith("y"):
			ytdlp_print_full_output = True
			
		else:
			ytdlp_print_full_output = False
			
		urls_all_count = len(urls_all)
		
		print(SEPARATOR_MAIN_SECTION)
		
		
		
		print("\nDownloading videos ...")
		
		for video_index, video_url in enumerate(urls_all, start=1):
			try:
				if video_index > 1:
					print(SEPARATOR_SUB_SECTION)
				
				print(f"\nProcessing video {video_index} of {urls_all_count}: {video_url} ...\n")
				
				ytdlp_args = [
					"--js-runtimes", f"deno:{deno_file_path}",
					"--ffmpeg-location", ffmpeg_file_path,
					# "--replace-in-metadata", "title", r"[^0-9A-Za-z ._-]", "_", # This was to ensure that the file name only contained certain characters.
					"--no-quiet", "--progress", "--newline", # Ensure that progress can be printed.
					"--paths", target_folder_path,
					"--windows-filenames",
					"--encoding", "utf-8", # Required to prevent Unicode characters in the output from being stripped out.
					"--print", "after_move:%(filepath)s", # Needed in order to check whether the file exists.
					video_url
				]
				
				if "youtube.com" in video_url:
					ytdlp_args.extend(["--output", "%(channel)s (%(upload_date>%Y∕%m∕%d)s)꞉ “%(title)s”.%(ext)s"]) # See https://mythofechelon.co.uk/blog/2020/3/6/how-to-work-around-windows-restricted-characters
				
				output_lines = []
				
				with subprocess.Popen([ytdlp_file_path, *ytdlp_args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=False) as ytdlp_process:
					for output_bytes in iter(ytdlp_process.stdout.readline, b""):
						output_line = output_bytes.decode("utf-8", errors="replace")
						
						if ytdlp_print_full_output:
							print(f"{video_index} of {urls_all_count}: {output_line}", end="")
						
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
					video_file_name = f'"{output_lines_last_path.name}"'
					
					print("\n" + PRINT_FORMAT_SUCCESS.format(message=f"Saved to file: {video_file_name}"))
					
					urls_succeeded.append(f"{video_url} → {video_file_name}")
			
			except Exception as error:
				print("\n" + PRINT_FORMAT_ERROR.format(message=str(error)))
				
				urls_failed.append(video_url)
			
				pass # No exceptions that can be handled.
			
		print(SEPARATOR_MAIN_SECTION)
		
		print("\nResults:")
		
		if urls_failed:
			print(f"\n{len(urls_failed)}/{len(urls_all)} failed:{SEPARATOR_LIST}{SEPARATOR_LIST.join(urls_failed)}")
		
		if urls_succeeded:
			print(f"\n{len(urls_succeeded)}/{len(urls_all)} succeeded:{SEPARATOR_LIST}{SEPARATOR_LIST.join(urls_succeeded)}")
		
		print(SEPARATOR_MAIN_SECTION)
		
		
		
if __name__ == "__main__":
	main()