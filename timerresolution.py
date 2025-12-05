import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path
import random

try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None
    filedialog = None


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def relaunch_as_admin():
    params = " ".join(f'"{a}"' for a in sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        f'"{Path(__file__).resolve()}" {params}',
        None,
        1,
    )
    sys.exit(0)


def select_folder(prompt: str):
    if tk is not None and filedialog is not None:
        root = tk.Tk()
        root.withdraw()
        root.update()
        path = filedialog.askdirectory(title=prompt)
        root.destroy()
        return path or None

    print(prompt)
    path = input("Enter full folder path (or leave empty to cancel): ").strip()
    return path or None


def safe_rmdir(path: str):
    if not path:
        return
    p = Path(path)
    if not p.exists():
        print(f"[INFO] Folder not found: {p}")
        return
    try:
        shutil.rmtree(p)
        print(f"[OK] Deleted folder: {p}")
    except Exception as e:
        print(f"[WARN] Failed to delete {p}: {e}")


def safe_del_glob(pattern: str):
    for p in Path("/").drive.glob(pattern) if hasattr(Path("/"), "drive") else []:
        try:
            if p.is_file():
                p.unlink()
        except Exception:
            pass


def run(cmd: str):
    subprocess.run(
        ["cmd", "/c", cmd],
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def reg_delete_matches(base_key: str, cheat_names):
    """Delete registry subkeys under base_key whose data matches any cheat name.

    Uses `reg query` with /f <name> /d and deletes each matching HKEY path.
    """
    if not cheat_names:
        return
    for stem in cheat_names:
        try:
            proc = subprocess.run(
                [
                    "reg",
                    "query",
                    base_key,
                    "/s",
                    "/f",
                    stem,
                    "/d",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=False,
            )
        except Exception:
            continue
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.upper().startswith("HKEY"):
                run(f'reg delete "{line}" /f')


def cleanup(cheat_name: str, cheat_binaries, extra_paths):
    env = os.environ
    userprofile = Path(env.get("UserProfile", ""))
    localappdata = Path(env.get("LOCALAPPDATA", ""))
    appdata = Path(env.get("APPDATA", ""))

    print("Starting deep cleanup process...\\n")
    cheat_names = []
    for name in cheat_binaries:
        stem = Path(name).stem
        if stem:
            cheat_names.append(stem)

    for p in extra_paths:
        print(f"Deleting additional folder: {p}...")
        safe_rmdir(p)

    if cheat_name == "potassium":
        pot_folder = localappdata / "Potassium"
        print(f"Deleting Potassium folder: {pot_folder}...")
        safe_rmdir(str(pot_folder))

    if cheat_name == "severe":
        print("Deleting C:\\v2 folder...")
        safe_rmdir("C:/v2")
        deps = localappdata / "dependencies"
        print(f"Deleting dependencies folder: {deps}...")
        safe_rmdir(str(deps))
        print("Deleting registry key HKEY_CURRENT_USER\\severe v2...")
        run(r"reg delete \"HKCU\\severe v2\" /f")

    if cheat_name == "assembly":
        print("Deleting C:\\assembly folder...")
        safe_rmdir("C:/assembly")

    if cheat_name == "matcha":
        print("Deleting C:\\matcha folder...")
        safe_rmdir("C:/matcha")

    if cheat_name == "ronin":
        ronin_folder = localappdata / "com.ronin.app"
        print(f"Deleting Ronin folder: {ronin_folder}...")
        safe_rmdir(str(ronin_folder))

    if cheat_name == "bunni":
        bunni_folder = localappdata / "com.bunni.app"
        print(f"Deleting Bunni folder: {bunni_folder}...")
        safe_rmdir(str(bunni_folder))

    print("Deleting BAM UserSettings for user accounts...")
    run(r"for /f \"tokens=*\" %%%%S in ('reg query \"HKLM\\SYSTEM\\CurrentControlSet\\Services\\bam\\State\\UserSettings\"') do reg delete \"%%%%S\" /f")
    print("BAM UserSettings cleanup attempted.")

    recent = appdata / "Microsoft" / "Windows" / "Recent"
    print(f"Cleaning {recent}...")
    if recent.is_dir():
        for f in recent.glob("*.*"):
            try:
                if f.is_file():
                    f.unlink()
            except Exception:
                pass

    print("Cleaning specific Prefetch files for selected cheeto...")
    prefetch = Path("C:/Windows/Prefetch")
    if prefetch.is_dir() and cheat_names:
        for pf in prefetch.glob("*.pf"):
            name_upper = pf.name.upper()
            if any(stem.upper() in name_upper for stem in cheat_names):
                try:
                    pf.unlink()
                    print(f"Deleted Prefetch: {pf.name}")
                except Exception:
                    pass

    print("Cleaning thumbnail cache...")
    explorer_dir = localappdata / "Microsoft" / "Windows" / "Explorer"
    for f in explorer_dir.glob("thumbcache_*.db"):
        try:
            f.unlink()
        except Exception:
            pass

    print("Cleaning icon cache...")
    run(fr"attrib -h -s -r \"{localappdata / 'IconCache.db'}\"")
    (localappdata / "IconCache.db").unlink(missing_ok=True)
    run(fr"attrib -h -s -r \"{explorer_dir / 'iconcache*'}\"")
    for f in explorer_dir.glob("iconcache*"):
        try:
            f.unlink()
        except Exception:
            pass

    print("Cleaning Jump Lists...")
    run(fr"del /f /q \"{(recent / 'AutomaticDestinations' / '*.automaticDestinations-ms')}\"")
    run(fr"del /f /q \"{(recent / 'CustomDestinations' / '*.customDestinations-ms')}\"")

    print("Cleaning Shell BagMRU entries (filtered by cheat names)...")
    reg_delete_matches(
        r"HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\BagMRU",
        cheat_names,
    )

    print("Cleaning OpenSavePidlMRU entries (filtered by cheat names)...")
    reg_delete_matches(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU",
        cheat_names,
    )

    print("Removing Windows Defender DisableAntiSpyware registry value...")
    run(r"reg delete \"HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\" /v DisableAntiSpyware /f")

    print("Cleaning Windows Explorer history (TypedPaths/RunMRU/RecentDocs, filtered)...")
    reg_delete_matches(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths",
        cheat_names,
    )
    reg_delete_matches(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU",
        cheat_names,
    )
    reg_delete_matches(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs",
        cheat_names,
    )

    print("Cleaning Shell bags (filtered by cheat names)...")
    reg_delete_matches(
        r"HKCU\Software\Microsoft\Windows\Shell\Bags",
        cheat_names,
    )

    print("Cleaning Start Menu history (filtered by cheat names)...")
    reg_delete_matches(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\StartPage",
        cheat_names,
    )
    reg_delete_matches(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\StartPage2",
        cheat_names,
    )

    print("Cleaning File Explorer address bar history (filtered)...")
    reg_delete_matches(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU",
        cheat_names,
    )
    reg_delete_matches(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRULegacy",
        cheat_names,
    )

    print("Cleaning MUICache (filtered by cheat names)...")
    reg_delete_matches(
        r"HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache",
        cheat_names,
    )

    print("Cleaning DNS Cache...")
    run("ipconfig /flushdns")

    print("Removing any remaining registry references (AppSwitched) for selected cheeto...")
    for stem in cheat_names:
        cmd = (
            'reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FeatureUsage\\AppSwitched" '
            f'/f "{stem}" /s /d && '
            'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FeatureUsage\\AppSwitched" /f'
        )
        run(cmd)

    print("Cleaning Program Compatibility Assistant history (filtered by cheat names)...")
    reg_delete_matches(
        r"HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Compatibility Assistant\Store",
        cheat_names,
    )

    print("Stopping Explorer for final cleanup...")
    run("taskkill /f /im explorer.exe")

    print("Resetting Amcache hive (stop appidsvc, rename, restart)...")
    run("net stop appidsvc /y")
    amcache = Path(r"C:\\Windows\\AppCompat\\Programs\\Amcache.hve")
    if amcache.exists():
        suffix = random.randint(1000, 9999)
        backup_name = f"Amcache_backup_{suffix}.hve"
        backup_path = amcache.with_name(backup_name)
        try:
            amcache.rename(backup_path)
            print(f"Renamed Amcache.hve to {backup_name}")
            try:
                backup_path.unlink()
                print(f"Deleted backup hive {backup_name}")
            except Exception as e:
                print(f"Failed to delete backup hive {backup_name}: {e}")
        except Exception as e:
            print(f"Failed to rename Amcache.hve: {e}")
    run("net start appidsvc")

    print("Deleting CrashDumps...")
    crash_dumps = userprofile / "AppData" / "Local" / "CrashDumps"
    safe_rmdir(str(crash_dumps))

    print("Stopping EventLog service...")
    run("net stop \"EventLog\" /y")

    print("Nuking USN Journal (C:)...")
    run("fsutil usn deletejournal /d /noprogress C:")

    print("Nuking all .evtx files...")
    run(r"del /f /q /s \"C:\\Windows\\System32\\winevt\\Logs\\*.evtx\"")

    print("Restarting EventLog service...")
    run("net start \"EventLog\"")

    print("Deleting ConsoleHost history...")
    console_hist = userprofile / "AppData" / "Roaming" / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt"
    console_hist.unlink(missing_ok=True)

    print("Clearing system memory (GC in .NET via PowerShell)...")
    run("powershell -Command \"& {[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()}\"")
    
    print("Restarting Explorer...")
    run("start explorer.exe")

    print("\n=======================================================")
    print("          Deep system cleanup completed!")
    print("=======================================================")
    print("All traces for the selected cheeto should be removed, including:")
    print("- Known folders and any extra paths you listed")
    print("- Prefetch, Explorer history, and related registry traces where possible")
    print("If you still see references, a system restart is recommended.\n")



def main():
    if not is_admin():
        print("Requesting administrative privileges...")
        relaunch_as_admin()

    print("=======================================================")
    print("               Complete System Cleanup Utility")
    print("=======================================================")
    print("Running with Administrator privileges\n")

    game = None
    while game is None:
        print("What game are you trying this for?")
        print("Options: Roblox, Minecraft")
        ans = input("> ").strip().lower()
        if ans in {"roblox", "minecraft"}:
            game = ans
        else:
            print("Please type either 'Roblox' or 'Minecraft'.\n")
            
    cheat = None
    while cheat is None:
        print("Type out what cheeto you're using.")
        if game == "roblox":
            valid = [
                "potassium",
                "severe",
                "assembly",
                "matcha",
                "volcano",
                "matrix",
                "ronin",
                "bunni",
            ]
        else:
            valid = [
                "prestige",
            ]

        print("Options: " + ", ".join(v.title() for v in valid))
        ans = input("> ").strip().lower()
        if ans in valid:
            cheat = ans
        else:
            print("Please type one of the listed options exactly (not case sensitive).\n")

    cheat_binaries_map = {
        "potassium": ["Potassium.exe", "Decompiler.exe"],
        "severe": ["software.exe", "upgrade.exe"],
        "assembly": ["client.exe"],
        "matcha": ["app.exe"],
        "volcano": ["VolcanoUI.exe", "VolcanoUpdater.exe"],
        "matrix": ["newui.exe", "oldui.exe"],
        "ronin": ["RoninV3.exe", "ronin.exe", "yt-dlp.exe"],
        "bunni": ["Bunni.exe", "bunni-installer.exe"],
        "prestige": ["Prestige-Injector.exe"],
    }

    cheat_binaries = cheat_binaries_map.get(cheat, [])
    
    extra_paths = []
    while True:
        print("\\n=======================================================")
        print("Do you want to type another folder path to delete? (y/n)")
        choice = input("> ").strip().lower()
        if choice not in {"y", "yes"}:
            break
        p = input("Enter full folder path (leave empty to cancel): ").strip().strip('"')
        if p:
            extra_paths.append(p)
            print(f"Queued for deletion: {p}")
        else:
            print("No folder provided.")

    cleanup(cheat, cheat_binaries, extra_paths)


if __name__ == "__main__":
    main()
    
