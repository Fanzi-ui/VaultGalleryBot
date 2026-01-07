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


def normalize_authorized_users(value: str) -> tuple[bool, str, str]:
    if not value.strip():
        return False, "AUTHORIZED_USERS is required.", ""
    parts = []
    for item in value.replace(",", " ").split():
        item = item.strip()
        if not item:
            continue
        if not item.isdigit():
            return (
                False,
                "AUTHORIZED_USERS must be numeric IDs separated by commas or spaces.",
                "",
            )
        parts.append(item)
    if not parts:
        return False, "AUTHORIZED_USERS is required.", ""
    return True, "", ",".join(parts)


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
    print("Use your own BotFather bot token; keep it private.")
    print("AUTHORIZED_USERS expects numeric Telegram IDs.")
    print("Web admin credentials use defaults from the README.")

    bot_token = ""
    while not bot_token:
        bot_token = prompt_value("BOT_TOKEN", "", True)
        if not bot_token:
            print("BOT_TOKEN is required.")

    default_users = ""
    authorized_users = prompt_value("AUTHORIZED_USERS", default_users)
    ok, error, authorized_users = normalize_authorized_users(authorized_users)
    if not ok:
        print(error)
        return 1

    web_admin_token = coalesce_value(
        current, defaults, "WEB_ADMIN_TOKEN", "some_random_secret"
    )
    web_admin_user = coalesce_value(current, defaults, "WEB_ADMIN_USER", "admin")
    web_admin_pass = coalesce_value(current, defaults, "WEB_ADMIN_PASS", "pass123")

    content = "\n".join(
        [
            f"BOT_TOKEN={bot_token}",
            f"AUTHORIZED_USERS={authorized_users}",
            f"WEB_ADMIN_TOKEN={web_admin_token}",
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
        text=(
            "Use your own BotFather bot token. "
            "AUTHORIZED_USERS should be numeric Telegram IDs."
        ),
        wraplength=420,
        justify="left",
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=6)

    fields = {}

    def add_field(row: int, label: str, key: str, default_value: str, secret: bool = False):
        tk.Label(root, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=6)
        var = tk.StringVar(value=default_value)
        entry = tk.Entry(root, textvariable=var, width=48, show="*" if secret else "")
        entry.grid(row=row, column=1, sticky="ew", padx=8, pady=6)
        fields[key] = var

    add_field(1, "BOT_TOKEN", "BOT_TOKEN", "", True)
    add_field(
        2,
        "AUTHORIZED_USERS",
        "AUTHORIZED_USERS",
        "",
        False,
    )
    web_admin_token = coalesce_value(
        current, defaults, "WEB_ADMIN_TOKEN", "some_random_secret"
    )
    web_admin_user = coalesce_value(current, defaults, "WEB_ADMIN_USER", "admin")
    web_admin_pass = coalesce_value(current, defaults, "WEB_ADMIN_PASS", "pass123")

    def on_save() -> None:
        bot_token = fields["BOT_TOKEN"].get().strip()
        authorized_users = fields["AUTHORIZED_USERS"].get().strip()
        if not bot_token:
            messagebox.showerror("Missing BOT_TOKEN", "BOT_TOKEN is required.")
            return

        ok, error, authorized_users = normalize_authorized_users(authorized_users)
        if not ok:
            messagebox.showerror("Invalid AUTHORIZED_USERS", error)
            return

        content = "\n".join(
            [
                f"BOT_TOKEN={bot_token}",
                f"AUTHORIZED_USERS={authorized_users}",
                f"WEB_ADMIN_TOKEN={web_admin_token}",
                f"WEB_ADMIN_USER={web_admin_user}",
                f"WEB_ADMIN_PASS={web_admin_pass}",
                "",
            ]
        )
        ENV_FILE.write_text(content)
        messagebox.showinfo("Saved", f"Wrote {ENV_FILE}.")
        root.destroy()

    def on_cancel() -> None:
        root.destroy()

    button_frame = tk.Frame(root)
    button_frame.grid(row=6, column=0, columnspan=2, pady=10)

    tk.Button(button_frame, text="Save", command=on_save, width=12).pack(
        side="left", padx=6
    )
    tk.Button(button_frame, text="Cancel", command=on_cancel, width=12).pack(
        side="left", padx=6
    )

    root.mainloop()
    return 0


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
