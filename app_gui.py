import os
import json
import subprocess
import traceback
import customtkinter as ctk

# --- Modern UI Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"
LOG_FILE = "error_log.txt"

class ControlPanelApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Video Generator - Control Panel v2.7")
        self.geometry("980x740") 
        self.resizable(False, False)

        # Main Title Header
        self.title_label = ctk.CTkLabel(self, text="AI Automation Settings Panel", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.pack(side="top", pady=(15, 10))

        # ==========================================
        # FOOTER (Save Button - Locked at BOTTOM first)
        # ==========================================
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(side="bottom", fill="x", padx=20, pady=(5, 15))

        self.save_btn = ctk.CTkButton(
            self.footer, 
            text="💾 Save Configurations & Deploy settings to Git Cloud Server", 
            fg_color="#2ecc71", hover_color="#27ae60",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45, command=self.save_and_push
        )
        self.save_btn.pack(fill="x")

        self.status_lbl = ctk.CTkLabel(self.footer, text="Status: Connected | Systems Initialized", text_color="gray", font=ctk.CTkFont(size=11))
        self.status_lbl.pack(pady=(8,0))


        # ==========================================
        # Main Layout Container
        # ==========================================
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 10))
        self.main_container.grid_columnconfigure((0, 1), weight=1)

        # Mapping frames safely 
        self.col_left = ctk.CTkFrame(self.main_container)
        self.col_left.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")

        self.col_right = ctk.CTkFrame(self.main_container)
        self.col_right.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")


        # ==========================================
        # LEFT COLUMN (Data & Content Filters)
        # ==========================================
        ctk.CTkLabel(self.col_left, text="Content & Feed Filters", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 5))

        # ১. RSS URLs
        self._create_label(self.col_left, "Target RSS Feed URLs (comma separated):")
        self.url_entry = ctk.CTkEntry(self.col_left, height=32)
        self.url_entry.pack(fill="x", padx=20, pady=(0, 12))

        # ২. Title Exclude Keywords
        self._create_label(self.col_left, "Exclude Keywords in Title (comma separated):")
        self.keyword_entry = ctk.CTkEntry(self.col_left, height=32)
        self.keyword_entry.pack(fill="x", padx=20, pady=(0, 12))

        # ৩. Body Exclude Keywords
        self._create_label(self.col_left, "Exclude Keywords inside Article (comma separated):")
        self.body_keyword_entry = ctk.CTkEntry(self.col_left, height=32)
        self.body_keyword_entry.pack(fill="x", padx=20, pady=(0, 12))

        self.num_group = ctk.CTkFrame(self.col_left, fg_color="transparent")
        self.num_group.pack(fill="x", padx=18, pady=(0, 12))
        self.num_group.grid_columnconfigure((0, 1), weight=1)
        
        # ৪. Minimum Word
        f_minword = ctk.CTkFrame(self.num_group, fg_color="transparent")
        f_minword.grid(row=0, column=0, sticky="ew", padx=2)
        self._create_label(f_minword, "Min Article Word Count:")
        self.word_count_entry = ctk.CTkEntry(f_minword, height=32)
        self.word_count_entry.pack(fill="x")
        
        # ৫. Max Age Hours
        f_age = ctk.CTkFrame(self.num_group, fg_color="transparent")
        f_age.grid(row=0, column=1, sticky="ew", padx=2)
        self._create_label(f_age, "Max Article Age (Hours):")
        self.age_entry = ctk.CTkEntry(f_age, height=32)
        self.age_entry.pack(fill="x")

        # Image Search Appender Settings
        ctk.CTkLabel(self.col_left, text="Advanced AI Image Search", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1abc9c").pack(pady=(15, 5))
        
        self.switch_var = ctk.IntVar(value=1)
        self.append_toggle = ctk.CTkSwitch(self.col_left, text="Append Suffix if subject is NOT a player name", 
                                           command=self._toggle_suffix, variable=self.switch_var, font=ctk.CTkFont(size=12))
        self.append_toggle.pack(anchor="w", padx=20, pady=(5, 5))
        
        self.suffix_entry = ctk.CTkEntry(self.col_left, height=32, placeholder_text="e.g. Wallpapers, Stadium HD, Court etc.")
        self.suffix_entry.pack(fill="x", padx=20, pady=(0, 12))


        # ==========================================
        # RIGHT COLUMN (Style, Audio & Look)
        # ==========================================
        ctk.CTkLabel(self.col_right, text="Voice & Aesthetic Styling", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 5))

        # ৬. AI Voice
        self._create_label(self.col_right, "AI Speaker / Voice Selection:")
        self.voice_combo = ctk.CTkComboBox(self.col_right, values=[
            "en-US-BrianNeural (US Male - Deep/Professional)",
            "en-US-GuyNeural (US Male - Casual)",
            "en-GB-RyanNeural (UK Male - Elegant)",
            "en-US-EricNeural (US Male - Sports Energy)"
        ], height=32)
        self.voice_combo.pack(fill="x", padx=20, pady=(0, 12))

        self.color_group = ctk.CTkFrame(self.col_right, fg_color="transparent")
        self.color_group.pack(fill="x", padx=18, pady=(0, 12))
        self.color_group.grid_columnconfigure((0, 1), weight=1)

        # ७. Sub Color
        f_tcolor = ctk.CTkFrame(self.color_group, fg_color="transparent")
        f_tcolor.grid(row=0, column=0, sticky="ew", padx=2)
        self._create_label(f_tcolor, "Subtitle Color (HEX):")
        self.text_color_entry = ctk.CTkEntry(f_tcolor, height=32)
        self.text_color_entry.pack(fill="x")

        # ৮. Background Box Color
        f_bcolor = ctk.CTkFrame(self.color_group, fg_color="transparent")
        f_bcolor.grid(row=0, column=1, sticky="ew", padx=2)
        self._create_label(f_bcolor, "Overlay Color (HEX):")
        self.bg_color_entry = ctk.CTkEntry(f_bcolor, height=32)
        self.bg_color_entry.pack(fill="x")

        # ৯. Overlay Style
        self._create_label(self.col_right, "Subtitle Visual Style Template:")
        self.style_combo = ctk.CTkComboBox(self.col_right, values=["Semi-Transparent Box (Style 3)", "Outline + Drop Shadow (Style 1)"], height=32)
        self.style_combo.pack(fill="x", padx=20, pady=(0, 10))

        # --- Dynamic UI Sliders Panel with Custom Feedback ---
        self.sliders_bg = ctk.CTkFrame(self.col_right, fg_color="#2b2b2b", corner_radius=6)
        self.sliders_bg.pack(fill="x", padx=20, pady=(0, 5))

        # ৯.৫ SFX Volume Slider Box
        f_sfx = ctk.CTkFrame(self.sliders_bg, fg_color="transparent")
        f_sfx.pack(fill="x", padx=15, pady=(8,0))
        ctk.CTkLabel(f_sfx, text="SFX Background Audio Level", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        self.val_sfx = ctk.CTkLabel(f_sfx, text="0%", font=ctk.CTkFont(size=12, weight="bold"), text_color="#1abc9c")
        self.val_sfx.pack(side="right")
        self.sfx_volume_slider = ctk.CTkSlider(self.sliders_bg, from_=0.0, to=1.0, number_of_steps=100, command=self._update_sfx, button_color="#1abc9c")
        self.sfx_volume_slider.pack(padx=15, pady=(0, 5), fill="x")

        # ৯.৮ Overlay Opacity 
        f_opac = ctk.CTkFrame(self.sliders_bg, fg_color="transparent")
        f_opac.pack(fill="x", padx=15, pady=(8,0))
        ctk.CTkLabel(f_opac, text="Subtitle Overlay Opacity", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        self.val_opac = ctk.CTkLabel(f_opac, text="0%", font=ctk.CTkFont(size=12, weight="bold"), text_color="#f39c12")
        self.val_opac.pack(side="right")
        self.bg_opacity_slider = ctk.CTkSlider(self.sliders_bg, from_=0.0, to=1.0, number_of_steps=100, command=self._update_opacity, button_color="#f39c12", button_hover_color="#e67e22")
        self.bg_opacity_slider.pack(padx=15, pady=(0, 5), fill="x")

        # ১০. Sub Margin Space Slider Box
        f_margin = ctk.CTkFrame(self.sliders_bg, fg_color="transparent")
        f_margin.pack(fill="x", padx=15, pady=(8,0))
        ctk.CTkLabel(f_margin, text="Subtitle Screen Spacing (Margin-Y)", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        self.val_margin = ctk.CTkLabel(f_margin, text="0px", font=ctk.CTkFont(size=12, weight="bold"), text_color="#3498db")
        self.val_margin.pack(side="right")
        self.margin_v_slider = ctk.CTkSlider(self.sliders_bg, from_=20, to=150, number_of_steps=26, command=self._update_margin)
        self.margin_v_slider.pack(padx=15, pady=(0, 5), fill="x")
        
        # ১১. Font Size Box
        f_size = ctk.CTkFrame(self.sliders_bg, fg_color="transparent")
        f_size.pack(fill="x", padx=15, pady=(8,0))
        ctk.CTkLabel(f_size, text="Subtitle Typography Font Size", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        self.val_size = ctk.CTkLabel(f_size, text="0px", font=ctk.CTkFont(size=12, weight="bold"), text_color="#e74c3c")
        self.val_size.pack(side="right")
        self.font_size_slider = ctk.CTkSlider(self.sliders_bg, from_=12, to=36, number_of_steps=24, command=self._update_size, button_color="#e74c3c", button_hover_color="#c0392b")
        self.font_size_slider.pack(padx=15, pady=(0, 10), fill="x")

        self.load_defaults()

    # --- Live Update Label Functions for Sliders ---
    def _update_sfx(self, val):
        self.val_sfx.configure(text=f"{int(float(val) * 100)}%")

    def _update_opacity(self, val):
        self.val_opac.configure(text=f"{int(float(val) * 100)}%")

    def _update_margin(self, val):
        self.val_margin.configure(text=f"{int(float(val))}px space")

    def _update_size(self, val):
        self.val_size.configure(text=f"{int(float(val))}px Size")
    # ---------------------------------------------

    def _create_label(self, parent, text_str):
        label = ctk.CTkLabel(parent, text=text_str, font=ctk.CTkFont(size=11, weight="bold"), text_color="#A9A9A9")
        label.pack(anchor="w", padx=24 if parent in [getattr(self, 'col_left', None), getattr(self, 'col_right', None)] else 2, pady=(8, 2))
        return label

    def _toggle_suffix(self):
        if self.switch_var.get() == 1:
            self.suffix_entry.configure(state="normal", placeholder_text="e.g. Wallpapers, Stadium HD etc.")
        else:
            self.suffix_entry.configure(state="disabled", placeholder_text="(Feature Disabled by Switch)")

    def load_defaults(self):
        sfx_val_loaded = 0.3
        opac_val_loaded = 0.6
        mar_val_loaded = 45
        fsize_val_loaded = 22
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.url_entry.insert(0, data.get("rss_urls", ""))
                self.keyword_entry.insert(0, data.get("exclude_title_keywords", ""))
                self.body_keyword_entry.insert(0, data.get("exclude_body_keywords", ""))
                self.word_count_entry.insert(0, str(data.get("min_word_count", 200)))
                self.age_entry.insert(0, str(data.get("max_age_hours", 24.0)))
                self.voice_combo.set(data.get("voice", ""))
                self.text_color_entry.insert(0, data.get("font_color", ""))
                self.bg_color_entry.insert(0, data.get("bg_color", ""))
                self.style_combo.set("Semi-Transparent Box (Style 3)" if data.get("border_style") == 3 else "Outline + Drop Shadow (Style 1)")
                
                sfx_val_loaded = float(data.get("sfx_volume", 0.3))
                opac_val_loaded = float(data.get("bg_opacity", 0.6))
                fsize_val_loaded = float(data.get("font_size", 22))
                mar_val_loaded = float(data.get("margin_v", 45))
                
                if data.get("append_keyword_feature", False):
                    self.append_toggle.select()
                else:
                    self.append_toggle.deselect()
                self._toggle_suffix()
                
                self.suffix_entry.delete(0, 'end')
                self.suffix_entry.insert(0, data.get("append_word_suffix", ""))
                
            except Exception:
                pass
        else:
            self.url_entry.insert(0, "https://sports.yahoo.com/nba/rss.xml")
            self.keyword_entry.insert(0, "odds, fantasy, betting")
            self.body_keyword_entry.insert(0, "arrested")
            self.word_count_entry.insert(0, "200")
            self.age_entry.insert(0, "24") 
            self.text_color_entry.insert(0, "#FFFFFF")
            self.bg_color_entry.insert(0, "#000000")
            self.style_combo.set("Semi-Transparent Box (Style 3)")
            self.append_toggle.select() 
            self._toggle_suffix()

        self.sfx_volume_slider.set(sfx_val_loaded)
        self.bg_opacity_slider.set(opac_val_loaded)
        self.font_size_slider.set(fsize_val_loaded)
        self.margin_v_slider.set(mar_val_loaded)

        self._update_sfx(sfx_val_loaded)
        self._update_opacity(opac_val_loaded)
        self._update_margin(mar_val_loaded)
        self._update_size(fsize_val_loaded)

    def save_and_push(self):
        self.save_btn.configure(state="disabled")
        self.status_lbl.configure(text="Processing Save Event... Pinging Github Connection.", text_color="yellow")
        self.update()

        border_style = 3 if "Box" in self.style_combo.get() else 1
        
        try:
            min_word_val = int(self.word_count_entry.get().strip())
        except ValueError:
            min_word_val = 200

        try:
            max_age_val = float(self.age_entry.get().strip())
        except ValueError:
            max_age_val = 24.0

        config_data = {
            "rss_urls": self.url_entry.get().strip(),
            "exclude_title_keywords": self.keyword_entry.get().strip(),
            "exclude_body_keywords": self.body_keyword_entry.get().strip(),
            "min_word_count": min_word_val,
            "max_age_hours": max_age_val,
            "voice": self.voice_combo.get().split(" ")[0],
            "font_color": self.text_color_entry.get().strip(),
            "bg_color": self.bg_color_entry.get().strip(),
            "border_style": border_style,
            "bg_opacity": float(self.bg_opacity_slider.get()),  
            "sfx_volume": float(self.sfx_volume_slider.get()),
            "font_size": int(self.font_size_slider.get()),
            "margin_v": int(self.margin_v_slider.get()),
            "append_keyword_feature": bool(self.switch_var.get()),
            "append_word_suffix": self.suffix_entry.get().strip() if bool(self.switch_var.get()) else ""
        }

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)

        try:
            subprocess.run(["git", "add", CONFIG_FILE], check=True)
            subprocess.run(["git", "commit", "-m", "Control Panel configuration sync pushed [skip ci]"], check=True)
            subprocess.run(["git", "push"], check=True)
            self.status_lbl.configure(text="[SUCCESS] Configuration File verified and cloud-synced cleanly via Github.", text_color="#2ecc71")
        except Exception as e:
            self.status_lbl.configure(text="[LOCAL SAVED] Configuration kept correctly. Push to github skipped or failed.", text_color="orange")
            with open(LOG_FILE, "a") as lf:
                lf.write(traceback.format_exc() + "\n")
        finally:
            self.save_btn.configure(state="normal")

if __name__ == "__main__":
    app = ControlPanelApp()
    app.mainloop()