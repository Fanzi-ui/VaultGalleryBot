from pathlib import Path
import sys

try:
    import tkinter as tk
    from tkinter import messagebox
    TK_AVAILABLE = True
except Exception:  # noqa: BLE001
    TK_AVAILABLE = False


ENV_FILE = Path(".env")
EXAMPLE_FILE = Path(".env.example")


def load_env_file(path: Path) -> dict:
    values = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def prompt_value(key: str, default_value: str = "", secret: bool = False) -> str:
    prompt_suffix = f" [{default_value}]" if default_value else ""
    if secret:
        import getpass

        value = getpass.getpass(f"{key}{prompt_suffix}: ").strip()
    else:
        value = input(f"{key}{prompt_suffix}: ").strip()
    return value or default_value


def coalesce_value(current: dict, defaults: dict, key: str, fallback: str = "") -> str:
    value = current.get(key, "").strip()
    if value:
        return value
    return defaults.get(key, fallback)


def ensure_env_cli() -> int:
    defaults = load_env_file(EXAMPLE_FILE)
    current = load_env_file(ENV_FILE)

    print("VaultGalleryBot installer (CLI fallback)")
    print("----------------------------------------")
    print("Leave a prompt empty to use the default value.")
    print("Web admin credentials use defaults from the README.")

    web_admin_token = coalesce_value(
        current, defaults, "WEB_ADMIN_TOKEN", "some_random_secret"
    )
    web_admin_user = coalesce_value(current, defaults, "WEB_ADMIN_USER", "admin")
    web_admin_pass = coalesce_value(current, defaults, "WEB_ADMIN_PASS", "pass123")

    web_admin_token = prompt_value("WEB_ADMIN_TOKEN", web_admin_token)
    web_admin_user = prompt_value("WEB_ADMIN_USER", web_admin_user)
    web_admin_pass = prompt_value("WEB_ADMIN_PASS", web_admin_pass, True)

    content = "\n".join(
        [
            f"WEB_ADMIN_TOKEN={web_admin_token or 'some_random_secret'}",
            f"WEB_ADMIN_USER={web_admin_user or 'admin'}",
            f"WEB_ADMIN_PASS={web_admin_pass or 'pass123'}",
            "",
        ]
    )
    ENV_FILE.write_text(content)
    print(f"Wrote {ENV_FILE}.")
    return 0


def ensure_env_gui() -> int:
    defaults = load_env_file(EXAMPLE_FILE)
    current = load_env_file(ENV_FILE)

    root = tk.Tk()
    root.title("VaultGalleryBot Installer")
    root.resizable(False, False)
    tk.Label(
        root,
        text="Configure web admin credentials for the API and dashboard.",
        wraplength=420,
        justify="left",
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=6)

    fields = {}
    saved = {"ok": False}

    def add_field(row: int, label: str, key: str, default_value: str, secret: bool = False):
        tk.Label(root, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=6)
        var = tk.StringVar(value=default_value)
        entry = tk.Entry(root, textvariable=var, width=48, show="*" if secret else "")
        entry.grid(row=row, column=1, sticky="ew", padx=8, pady=6)
        fields[key] = var

    web_admin_token = coalesce_value(
        current, defaults, "WEB_ADMIN_TOKEN", "some_random_secret"
    )
    web_admin_user = coalesce_value(current, defaults, "WEB_ADMIN_USER", "admin")
    web_admin_pass = coalesce_value(current, defaults, "WEB_ADMIN_PASS", "pass123")
    add_field(1, "WEB_ADMIN_TOKEN", "WEB_ADMIN_TOKEN", web_admin_token, True)
    add_field(2, "WEB_ADMIN_USER", "WEB_ADMIN_USER", web_admin_user, False)
    add_field(3, "WEB_ADMIN_PASS", "WEB_ADMIN_PASS", web_admin_pass, True)

    def on_save() -> None:
        web_admin_token_value = fields["WEB_ADMIN_TOKEN"].get().strip()
        web_admin_user_value = fields["WEB_ADMIN_USER"].get().strip()
        web_admin_pass_value = fields["WEB_ADMIN_PASS"].get().strip()

        content = "\n".join(
            [
                f"WEB_ADMIN_TOKEN={web_admin_token_value or web_admin_token}",
                f"WEB_ADMIN_USER={web_admin_user_value or web_admin_user}",
                f"WEB_ADMIN_PASS={web_admin_pass_value or web_admin_pass}",
                "",
            ]
        )
        ENV_FILE.write_text(content)
        messagebox.showinfo("Saved", f"Wrote {ENV_FILE}.")
        saved["ok"] = True
        root.destroy()

    def on_cancel() -> None:
        saved["ok"] = False
        root.destroy()

    button_frame = tk.Frame(root)
    button_frame.grid(row=5, column=0, columnspan=2, pady=10)

    tk.Button(button_frame, text="Save", command=on_save, width=12).pack(
        side="left", padx=6
    )
    tk.Button(button_frame, text="Cancel", command=on_cancel, width=12).pack(
        side="left", padx=6
    )

    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.mainloop()
    return 0 if saved["ok"] else 1


if __name__ == "__main__":
    if TK_AVAILABLE:
        try:
            sys.exit(ensure_env_gui())
        except tk.TclError:
            print("GUI installer unavailable (no display). Falling back to CLI.")
            sys.exit(ensure_env_cli())
    else:
        print("GUI installer unavailable (missing Tk). Falling back to CLI.")
        sys.exit(ensure_env_cli())
