from pathlib import Path
import shutil
from meshroom.interaction import log


def generate_files_from_template(
    template_dir: Path,
    dst_dir: Path,
    placeholders: dict = {},
    overwrite_files: bool = False,
    overwrite_empty_files: bool = True,
):
    """Generate files from a directory of template, replacing placeholders"""
    log("\nGenerate files from template", template_dir, "to", dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for fn in template_dir.rglob("*"):
        dst_file = dst_dir / fn.relative_to(template_dir)

        # Generate directories (including empty ones)
        if fn.is_dir():
            log("    Generate directory", dst_file)
            dst_file.mkdir(parents=True, exist_ok=True)
            continue

        if not fn.is_file():
            continue

        # Handle existing files and overwritting options
        if dst_file.is_file() and not overwrite_files:
            continue
        if dst_file.is_file() and dst_file.read_text() != "" and not overwrite_empty_files:
            continue

        dst_file.parent.mkdir(parents=True, exist_ok=True)

        log("    Generate", dst_file)
        if fn.suffix == ".png":
            shutil.copy(fn, dst_file)
        else:
            # Replace placeholders
            try:
                text = fn.read_text()
                for k, v in placeholders.items():
                    text = text.replace(k, v)

                dst_file.write_text(text)
            except UnicodeDecodeError:
                pass  # Skip binary files
    print()
