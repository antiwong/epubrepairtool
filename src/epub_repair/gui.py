"""Simple GUI for EPUB Repair and Upgrade tools using Tkinter."""

import sys
import threading
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .cli import run_repair

try:
    from epub_upgrade.cli import parse_args
    from epub_upgrade.epub_io import copy_epub, extract_epub, get_opf_path, repackage_epub, verify_epub_file
    from epub_upgrade.reporting import Reporter as UpgradeReporter
    from epub_upgrade.upgrade import upgrade_to_epub3
    from epub_upgrade.versioning import detect_epub_version, load_opf
    UPGRADE_AVAILABLE = True
except ImportError:
    UPGRADE_AVAILABLE = False


class EpubRepairGUI:
    """Main GUI application for EPUB Repair and Upgrade."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("EPUB Tools - Repair & Upgrade")
        self.root.geometry("750x750")
        self.root.resizable(True, True)
        
        # Shared variables
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        
        # Repair variables
        self.mode = tk.StringVar(value="safe")
        self.report_path = tk.StringVar()
        self.generate_report = tk.BooleanVar(value=False)
        
        # Upgrade variables
        self.enable_upgrade = tk.BooleanVar(value=False)
        self.target_version = tk.StringVar(value="3.0")
        self.force_rewrite = tk.BooleanVar(value=False)
        self.dry_run = tk.BooleanVar(value=False)
        self.upgrade_report_path = tk.StringVar()
        self.generate_upgrade_report = tk.BooleanVar(value=False)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and layout all GUI widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="EPUB Tools - Repair & Upgrade",
            font=("Helvetica", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Shared file selection
        self._create_shared_widgets(main_frame)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.rowconfigure(2, weight=1)
        
        # Repair tab
        repair_frame = ttk.Frame(notebook, padding="10")
        notebook.add(repair_frame, text="Format Repair")
        repair_frame.columnconfigure(1, weight=1)
        self._create_repair_widgets(repair_frame)
        
        # Upgrade tab
        upgrade_frame = ttk.Frame(notebook, padding="10")
        notebook.add(upgrade_frame, text="Version Upgrade")
        upgrade_frame.columnconfigure(1, weight=1)
        if UPGRADE_AVAILABLE:
            self._create_upgrade_widgets(upgrade_frame)
        else:
            ttk.Label(
                upgrade_frame,
                text="EPUB Upgrade module not available",
                foreground="gray"
            ).grid(row=0, column=0, columnspan=3, pady=20)
        
        # Action buttons and status (below tabs)
        self._create_action_area(main_frame)
        
        # Results area (bottom)
        self._create_results_area(main_frame)
    
    def _create_shared_widgets(self, parent):
        """Create shared file selection widgets."""
        row = 0
        
        # Input file selection
        ttk.Label(parent, text="Input EPUB:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(parent, textvariable=self.input_path, width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(
            parent,
            text="Browse...",
            command=self._browse_input
        ).grid(row=row, column=2, pady=5)
        
        row += 1
        
        # Output file selection
        ttk.Label(parent, text="Output EPUB:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(parent, textvariable=self.output_path, width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(
            parent,
            text="Browse...",
            command=self._browse_output
        ).grid(row=row, column=2, pady=5)
    
    def _create_repair_widgets(self, parent):
        """Create widgets for repair tab."""
        row = 0
        
        # Mode selection
        mode_frame = ttk.LabelFrame(parent, text="Repair Mode", padding="10")
        mode_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Radiobutton(
            mode_frame,
            text="Safe (conservative fixes)",
            variable=self.mode,
            value="safe"
        ).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        ttk.Radiobutton(
            mode_frame,
            text="Aggressive (includes CSS cleanup)",
            variable=self.mode,
            value="aggressive"
        ).grid(row=1, column=0, sticky=tk.W, padx=5)
        
        row += 1
        
        # Report options
        report_frame = ttk.LabelFrame(parent, text="Report Options", padding="10")
        report_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        report_frame.columnconfigure(0, weight=1)
        
        ttk.Checkbutton(
            report_frame,
            text="Generate report file",
            variable=self.generate_report,
            command=self._toggle_report_path
        ).grid(row=0, column=0, sticky=tk.W)
        
        self.report_entry = ttk.Entry(
            report_frame,
            textvariable=self.report_path,
            width=50,
            state="disabled"
        )
        self.report_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.report_browse_btn = ttk.Button(
            report_frame,
            text="Browse...",
            command=self._browse_report,
            state="disabled"
        )
        self.report_browse_btn.grid(row=1, column=1, padx=5)
    
    def _create_upgrade_widgets(self, parent):
        """Create widgets for upgrade tab."""
        row = 0
        
        # Enable upgrade checkbox
        ttk.Checkbutton(
            parent,
            text="Enable EPUB version upgrade (EPUB 2 → EPUB 3)",
            variable=self.enable_upgrade
        ).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        row += 1
        
        # Upgrade options
        upgrade_options = ttk.LabelFrame(parent, text="Upgrade Options", padding="10")
        upgrade_options.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        upgrade_options.columnconfigure(1, weight=1)
        
        ttk.Label(upgrade_options, text="Target version:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        version_combo = ttk.Combobox(
            upgrade_options,
            textvariable=self.target_version,
            values=["3.0", "3.2", "3.3"],
            state="readonly",
            width=10
        )
        version_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Checkbutton(
            upgrade_options,
            text="Force rewrite (even if already EPUB 3)",
            variable=self.force_rewrite
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Checkbutton(
            upgrade_options,
            text="Dry run (detect version only, no changes)",
            variable=self.dry_run
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        row += 1
        
        # Upgrade report options
        upgrade_report_frame = ttk.LabelFrame(parent, text="Upgrade Report Options", padding="10")
        upgrade_report_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        upgrade_report_frame.columnconfigure(0, weight=1)
        
        ttk.Checkbutton(
            upgrade_report_frame,
            text="Generate upgrade report file",
            variable=self.generate_upgrade_report,
            command=self._toggle_upgrade_report_path
        ).grid(row=0, column=0, sticky=tk.W)
        
        self.upgrade_report_entry = ttk.Entry(
            upgrade_report_frame,
            textvariable=self.upgrade_report_path,
            width=50,
            state="disabled"
        )
        self.upgrade_report_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.upgrade_report_browse_btn = ttk.Button(
            upgrade_report_frame,
            text="Browse...",
            command=self._browse_upgrade_report,
            state="disabled"
        )
        self.upgrade_report_browse_btn.grid(row=1, column=1, padx=5)
    
    def _create_action_area(self, parent):
        """Create action buttons and status area."""
        row = 3
        
        # Buttons frame
        buttons_frame = ttk.Frame(parent)
        buttons_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        self.repair_button = ttk.Button(
            buttons_frame,
            text="Repair EPUB",
            command=self._run_repair,
            width=20
        )
        self.repair_button.pack(side=tk.LEFT, padx=5)
        
        if UPGRADE_AVAILABLE:
            self.upgrade_button = ttk.Button(
                buttons_frame,
                text="Upgrade EPUB",
                command=self._run_upgrade,
                width=20
            )
            self.upgrade_button.pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # Progress bar
        self.progress = ttk.Progressbar(
            parent,
            mode="indeterminate",
            length=400
        )
        self.progress.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        row += 1
        
        # Status label
        self.status_label = ttk.Label(parent, text="Ready")
        self.status_label.grid(row=row, column=0, columnspan=3, pady=5)
    
    def _create_results_area(self, parent):
        """Create results text area."""
        results_frame = ttk.LabelFrame(parent, text="Results", padding="10")
        results_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(5, weight=1)
        
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            height=10,
            wrap=tk.WORD,
            state="disabled"
        )
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def _browse_input(self):
        """Browse for input EPUB file."""
        filename = filedialog.askopenfilename(
            title="Select Input EPUB File",
            filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
        )
        if filename:
            self.input_path.set(filename)
            # Auto-suggest output path in the same folder as input
            input_path = Path(filename)
            output_path = input_path.parent / f"{input_path.stem}_repaired{input_path.suffix}"
            self.output_path.set(str(output_path))
    
    def _browse_output(self):
        """Browse for output EPUB file."""
        initial_dir = None
        initial_file = None
        if self.input_path.get():
            input_path = Path(self.input_path.get())
            initial_dir = str(input_path.parent)
            initial_file = f"{input_path.stem}_repaired{input_path.suffix}"
        
        filename = filedialog.asksaveasfilename(
            title="Save Output EPUB File",
            defaultextension=".epub",
            initialdir=initial_dir,
            initialfile=initial_file,
            filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
    
    def _browse_report(self):
        """Browse for report file."""
        filename = filedialog.asksaveasfilename(
            title="Save Report File",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.report_path.set(filename)
    
    def _browse_upgrade_report(self):
        """Browse for upgrade report file."""
        filename = filedialog.asksaveasfilename(
            title="Save Upgrade Report File",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.upgrade_report_path.set(filename)
    
    def _toggle_report_path(self):
        """Enable/disable report path entry and browse button."""
        state = "normal" if self.generate_report.get() else "disabled"
        if not self.generate_report.get():
            self.report_path.set("")
        self.report_entry.config(state=state)
        self.report_browse_btn.config(state=state)
    
    def _toggle_upgrade_report_path(self):
        """Enable/disable upgrade report path entry and browse button."""
        state = "normal" if self.generate_upgrade_report.get() else "disabled"
        if not self.generate_upgrade_report.get():
            self.upgrade_report_path.set("")
        self.upgrade_report_entry.config(state=state)
        self.upgrade_report_browse_btn.config(state=state)
    
    def _update_status(self, message: str):
        """Update status label."""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def _append_result(self, message: str):
        """Append message to results text area."""
        self.results_text.config(state="normal")
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.see(tk.END)
        self.results_text.config(state="disabled")
        self.root.update_idletasks()
    
    def _run_repair(self):
        """Run the repair process in a separate thread."""
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select an input EPUB file.")
            return
        
        if not self.output_path.get():
            messagebox.showerror("Error", "Please specify an output EPUB file.")
            return
        
        input_path = Path(self.input_path.get())
        if not input_path.exists():
            messagebox.showerror("Error", f"Input file not found: {input_path}")
            return
        
        report_path = None
        if self.generate_report.get():
            if not self.report_path.get():
                messagebox.showerror("Error", "Please specify a report file path.")
                return
            report_path = Path(self.report_path.get())
        
        # Disable buttons and start progress
        self.repair_button.config(state="disabled")
        if UPGRADE_AVAILABLE:
            self.upgrade_button.config(state="disabled")
        self.progress.start()
        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state="disabled")
        
        thread = threading.Thread(
            target=self._repair_worker,
            args=(input_path, Path(self.output_path.get()), self.mode.get(), report_path),
            daemon=True
        )
        thread.start()
    
    def _run_upgrade(self):
        """Run the upgrade process in a separate thread."""
        if not UPGRADE_AVAILABLE:
            messagebox.showerror("Error", "EPUB Upgrade module not available")
            return
        
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select an input EPUB file.")
            return
        
        if not self.output_path.get():
            messagebox.showerror("Error", "Please specify an output EPUB file.")
            return
        
        input_path = Path(self.input_path.get())
        if not input_path.exists():
            messagebox.showerror("Error", f"Input file not found: {input_path}")
            return
        
        upgrade_report_path = None
        if self.generate_upgrade_report.get():
            if not self.upgrade_report_path.get():
                messagebox.showerror("Error", "Please specify an upgrade report file path.")
                return
            upgrade_report_path = Path(self.upgrade_report_path.get())
        
        # Disable buttons and start progress
        self.repair_button.config(state="disabled")
        self.upgrade_button.config(state="disabled")
        self.progress.start()
        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state="disabled")
        
        thread = threading.Thread(
            target=self._upgrade_worker,
            args=(
                input_path,
                Path(self.output_path.get()),
                self.target_version.get(),
                self.force_rewrite.get(),
                self.dry_run.get(),
                upgrade_report_path
            ),
            daemon=True
        )
        thread.start()
    
    def _repair_worker(self, input_path, output_path, mode, report_path):
        """Worker thread for repair process."""
        try:
            self._update_status("Starting repair...")
            self._append_result("=" * 60)
            self._append_result("EPUB Repair Process")
            self._append_result("=" * 60)
            self._append_result(f"Input: {input_path}")
            self._append_result(f"Output: {output_path}")
            self._append_result(f"Mode: {mode}")
            self._append_result("")
            
            summary = run_repair(
                input_path=input_path,
                output_path=output_path,
                mode=mode,
                report_path=report_path
            )
            
            self._append_result("Repair completed successfully!")
            self._append_result("")
            self._append_result("Summary:")
            self._append_result("-" * 60)
            
            if summary["counters"]:
                for category, count in sorted(summary["counters"].items()):
                    self._append_result(f"  {category}: {count}")
            else:
                self._append_result("  (No changes recorded)")
            
            self._append_result(f"\nTotal files modified: {summary['total_files_modified']}")
            
            if report_path:
                self._append_result(f"\nReport saved to: {report_path}")
            
            self._update_status("Repair completed successfully!")
            messagebox.showinfo(
                "Success",
                f"EPUB repair completed!\n\n"
                f"Output saved to: {output_path}\n"
                f"Files modified: {summary['total_files_modified']}"
            )
        
        except Exception as e:
            error_msg = f"Error: {e}"
            self._append_result(f"ERROR: {error_msg}")
            self._update_status("Error occurred")
            messagebox.showerror("Error", error_msg)
            import traceback
            self._append_result("\nTraceback:")
            self._append_result(traceback.format_exc())
        
        finally:
            self.progress.stop()
            self.repair_button.config(state="normal")
            if UPGRADE_AVAILABLE:
                self.upgrade_button.config(state="normal")
            self._update_status("Ready")
    
    def _upgrade_worker(self, input_path, output_path, target_version, force_rewrite, dry_run, report_path):
        """Worker thread for upgrade process."""
        try:
            self._update_status("Starting upgrade...")
            self._append_result("=" * 60)
            self._append_result("EPUB Upgrade Process")
            self._append_result("=" * 60)
            self._append_result(f"Input: {input_path}")
            self._append_result(f"Output: {output_path}")
            self._append_result(f"Target version: {target_version}")
            self._append_result(f"Force rewrite: {force_rewrite}")
            self._append_result(f"Dry run: {dry_run}")
            self._append_result("")
            
            # Verify EPUB
            verify_epub_file(input_path)
            
            if dry_run:
                # Dry run: only detect version
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    extract_epub(input_path, temp_path)
                    opf_path = get_opf_path(temp_path)
                    opf_tree = load_opf(opf_path)
                    normalized_version, raw_version = detect_epub_version(opf_tree)
                    
                    self._append_result(f"Detected version: {raw_version} ({normalized_version})")
                    if normalized_version == "3":
                        self._append_result("Status: Already EPUB 3, no upgrade needed")
                    else:
                        self._append_result(f"Status: Would upgrade to EPUB {target_version}")
                    
                    self._update_status("Dry run completed")
                    messagebox.showinfo("Dry Run", f"EPUB version detected: {raw_version}")
                return
            
            # Perform upgrade
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                extract_epub(input_path, temp_path)
                
                opf_path = get_opf_path(temp_path)
                opf_tree = load_opf(opf_path)
                normalized_version, raw_version = detect_epub_version(opf_tree)
                
                reporter = UpgradeReporter()
                reporter.set_versions(normalized_version, raw_version)
                
                needs_upgrade = normalized_version != "3" or force_rewrite
                
                if not needs_upgrade:
                    copy_epub(input_path, output_path)
                    reporter.note("File already EPUB 3, copied unchanged")
                else:
                    upgrade_to_epub3(temp_path, target_version, reporter, force_rewrite)
                    reporter.set_versions(normalized_version, raw_version, target_version)
                    repackage_epub(temp_path, output_path)
                
                # Print summary
                self._append_result("Upgrade completed successfully!")
                self._append_result("")
                self._append_result("Summary:")
                self._append_result("-" * 60)
                self._append_result(f"Original version: {raw_version} ({normalized_version})")
                self._append_result(f"New version: {reporter.data['new_version']}")
                
                if reporter.data["nav_converted"]:
                    self._append_result(f"Navigation: Converted NCX to nav.xhtml")
                
                if reporter.data["warnings"]:
                    self._append_result("\nWarnings:")
                    for warning in reporter.data["warnings"]:
                        self._append_result(f"  - {warning}")
                
                if reporter.data["notes"]:
                    self._append_result("\nNotes:")
                    for note in reporter.data["notes"]:
                        self._append_result(f"  - {note}")
                
                if report_path:
                    reporter.write_json(report_path)
                    self._append_result(f"\nReport saved to: {report_path}")
            
            self._update_status("Upgrade completed successfully!")
            messagebox.showinfo(
                "Success",
                f"EPUB upgrade completed!\n\n"
                f"Output saved to: {output_path}"
            )
        
        except Exception as e:
            error_msg = f"Error: {e}"
            self._append_result(f"ERROR: {error_msg}")
            self._update_status("Error occurred")
            messagebox.showerror("Error", error_msg)
            import traceback
            self._append_result("\nTraceback:")
            self._append_result(traceback.format_exc())
        
        finally:
            self.progress.stop()
            self.repair_button.config(state="normal")
            self.upgrade_button.config(state="normal")
            self._update_status("Ready")


def main():
    """Launch the GUI application."""
    root = tk.Tk()
    app = EpubRepairGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
