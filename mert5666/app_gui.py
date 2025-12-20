"""
Sahte Belge Tespit Sistemi - GUI
Tkinter tabanlı kullanıcı arayüzü
"""

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import cv2
import os
from forgery_detector import ForensicReport


class ForensicApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Sahte Belge Tespit Sistemi")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a2e')
        
        self.analyzer = ForensicReport()
        self.current_image = None
        self.results = None
        
        self.setup_styles()
        self.create_widgets()
    
    def setup_styles(self):
        """Stil ayarları"""
        self.colors = {
            'bg': '#1a1a2e',
            'card': '#16213e',
            'accent': '#0f3460',
            'text': '#e8e8e8',
            'success': '#00d26a',
            'warning': '#ffc300',
            'danger': '#ff4757'
        }
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Card.TFrame', background=self.colors['card'])
        style.configure('Title.TLabel', 
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 24, 'bold'))
        style.configure('Subtitle.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 12))
        style.configure('Score.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 48, 'bold'))
    
    def create_widgets(self):
        """Arayüz bileşenlerini oluştur"""
        
        # Ana container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Başlık
        title = ttk.Label(main_frame, text="🔍 Sahte Belge Tespit Sistemi",
                         style='Title.TLabel')
        title.pack(pady=(0, 20))
        
        # Üst panel - Butonlar
        btn_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        btn_frame.pack(fill='x', pady=(0, 20))
        
        self.load_btn = tk.Button(btn_frame, text="📁 Resim Seç",
                                  font=('Segoe UI', 12, 'bold'),
                                  bg=self.colors['accent'],
                                  fg='white',
                                  activebackground='#1a4a7e',
                                  activeforeground='white',
                                  relief='flat',
                                  padx=30, pady=10,
                                  cursor='hand2',
                                  command=self.load_image)
        self.load_btn.pack(side='left', padx=(0, 10))
        
        self.analyze_btn = tk.Button(btn_frame, text="🔬 Analiz Et",
                                     font=('Segoe UI', 12, 'bold'),
                                     bg='#00d26a',
                                     fg='white',
                                     activebackground='#00a854',
                                     activeforeground='white',
                                     relief='flat',
                                     padx=30, pady=10,
                                     cursor='hand2',
                                     state='disabled',
                                     command=self.analyze_image)
        self.analyze_btn.pack(side='left')
        
        # Dosya yolu label
        self.file_label = tk.Label(btn_frame, text="Henüz dosya seçilmedi",
                                   bg=self.colors['bg'],
                                   fg=self.colors['text'],
                                   font=('Segoe UI', 10))
        self.file_label.pack(side='right')
        
        # İçerik alanı
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill='both', expand=True)
        
        # Sol panel - Orijinal resim
        left_panel = tk.Frame(content_frame, bg=self.colors['card'], relief='flat')
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        tk.Label(left_panel, text="📷 Orijinal Resim",
                bg=self.colors['card'], fg=self.colors['text'],
                font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        self.original_canvas = tk.Canvas(left_panel, bg=self.colors['accent'],
                                         highlightthickness=0)
        self.original_canvas.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Sağ panel - Analiz sonuçları
        right_panel = tk.Frame(content_frame, bg=self.colors['card'], relief='flat')
        right_panel.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        tk.Label(right_panel, text="📊 Analiz Sonuçları",
                bg=self.colors['card'], fg=self.colors['text'],
                font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        # Sonuç alanı
        self.result_frame = tk.Frame(right_panel, bg=self.colors['card'])
        self.result_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Başlangıç mesajı
        self.placeholder = tk.Label(self.result_frame,
                                    text="Analiz için bir resim seçin\nve 'Analiz Et' butonuna tıklayın",
                                    bg=self.colors['card'],
                                    fg='#888888',
                                    font=('Segoe UI', 12),
                                    justify='center')
        self.placeholder.pack(expand=True)
        
        # Alt panel - Analiz haritaları için notebook
        self.notebook_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        self.notebook_frame.pack(fill='x', pady=(20, 0))
        
    def load_image(self):
        """Resim dosyası seç"""
        file_types = [
            ("Resim Dosyaları", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ("Tüm Dosyalar", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(filetypes=file_types)
        
        if file_path:
            self.current_image = file_path
            self.file_label.config(text=os.path.basename(file_path))
            self.analyze_btn.config(state='normal')
            
            # Resmi göster
            self.display_image(file_path, self.original_canvas)
            
            # Önceki sonuçları temizle
            self.clear_results()
    
    def display_image(self, path, canvas, max_size=400):
        """Resmi canvas'a göster"""
        img = Image.open(path)
        
        # Boyutları ayarla
        ratio = min(max_size / img.width, max_size / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        
        canvas.delete("all")
        canvas.config(width=new_size[0], height=new_size[1])
        canvas.create_image(new_size[0]//2, new_size[1]//2, image=photo)
        canvas.image = photo  # Referansı sakla
    
    def display_cv2_image(self, cv2_img, canvas, max_size=300):
        """OpenCV imajını canvas'a göster"""
        # BGR -> RGB
        img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img_rgb)
        
        # Boyutları ayarla
        ratio = min(max_size / img.width, max_size / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        
        canvas.delete("all")
        canvas.config(width=new_size[0], height=new_size[1])
        canvas.create_image(new_size[0]//2, new_size[1]//2, image=photo)
        canvas.image = photo
    
    def clear_results(self):
        """Sonuçları temizle"""
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        for widget in self.notebook_frame.winfo_children():
            widget.destroy()
    
    def analyze_image(self):
        """Resmi analiz et"""
        if not self.current_image:
            return
        
        # Butonları devre dışı bırak
        self.analyze_btn.config(state='disabled', text='⏳ Analiz Ediliyor...')
        self.root.update()
        
        try:
            # Analizi yap
            self.results = self.analyzer.full_analysis(self.current_image)
            
            # Sonuçları göster
            self.display_results()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Analiz sırasında hata oluştu:\n{str(e)}")
        
        finally:
            self.analyze_btn.config(state='normal', text='🔬 Analiz Et')
    
    def display_results(self):
        """Analiz sonuçlarını göster"""
        self.clear_results()
        
        # Genel skor
        score = self.results['overall_score']
        verdict = self.results['verdict']
        
        # Skor rengi
        if score < 20:
            score_color = self.colors['success']
        elif score < 60:
            score_color = self.colors['warning']
        else:
            score_color = self.colors['danger']
        
        # Skor gösterimi
        score_frame = tk.Frame(self.result_frame, bg=self.colors['card'])
        score_frame.pack(pady=20)
        
        tk.Label(score_frame, text="Şüphe Skoru",
                bg=self.colors['card'], fg='#888888',
                font=('Segoe UI', 12)).pack()
        
        tk.Label(score_frame, text=f"{score}",
                bg=self.colors['card'], fg=score_color,
                font=('Segoe UI', 64, 'bold')).pack()
        
        tk.Label(score_frame, text="/ 100",
                bg=self.colors['card'], fg='#888888',
                font=('Segoe UI', 14)).pack()
        
        # Karar
        tk.Label(self.result_frame, text=verdict,
                bg=self.colors['card'], fg=score_color,
                font=('Segoe UI', 14, 'bold'),
                wraplength=350).pack(pady=20)
        
        # Detaylı skorlar
        details_frame = tk.Frame(self.result_frame, bg=self.colors['card'])
        details_frame.pack(fill='x', padx=20, pady=10)
        
        scores = [
            ("ELA Analizi", self.results['ela'].get('score', 0)),
            ("Gürültü Analizi", self.results['noise'].get('score', 0)),
            ("Metadata Analizi", self.results['metadata'].get('score', 0)),
            ("Kenar Analizi", self.results['edge'].get('score', 0))
        ]
        
        for name, value in scores:
            row = tk.Frame(details_frame, bg=self.colors['card'])
            row.pack(fill='x', pady=5)
            
            tk.Label(row, text=name, bg=self.colors['card'],
                    fg=self.colors['text'], font=('Segoe UI', 10),
                    anchor='w', width=20).pack(side='left')
            
            # Progress bar
            progress = ttk.Progressbar(row, length=150, mode='determinate',
                                       value=value, maximum=100)
            progress.pack(side='left', padx=10)
            
            tk.Label(row, text=f"{value:.0f}%", bg=self.colors['card'],
                    fg=self.colors['text'], font=('Segoe UI', 10, 'bold'),
                    width=5).pack(side='left')
        
        # Metadata bilgileri
        if 'metadata' in self.results and 'info' in self.results['metadata']:
            meta = self.results['metadata']['info']
            if meta.get('software'):
                tk.Label(self.result_frame, 
                        text=f"📝 Yazılım: {meta['software']}",
                        bg=self.colors['card'], fg='#ff9f43',
                        font=('Segoe UI', 10)).pack(pady=5)
        
        # Analiz haritalarını göster
        self.display_heatmaps()
    
    def display_heatmaps(self):
        """Isı haritalarını göster"""
        maps_frame = tk.Frame(self.notebook_frame, bg=self.colors['bg'])
        maps_frame.pack(fill='x')
        
        tk.Label(maps_frame, text="🗺️ Analiz Haritaları",
                bg=self.colors['bg'], fg=self.colors['text'],
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        canvas_frame = tk.Frame(maps_frame, bg=self.colors['bg'])
        canvas_frame.pack(fill='x')
        
        maps = [
            ("ELA", self.results['ela'].get('heatmap')),
            ("Gürültü", self.results['noise'].get('heatmap')),
            ("Kenar", self.results['edge'].get('heatmap'))
        ]
        
        for i, (name, heatmap) in enumerate(maps):
            if heatmap is not None:
                frame = tk.Frame(canvas_frame, bg=self.colors['card'])
                frame.pack(side='left', padx=5, pady=5)
                
                tk.Label(frame, text=name, bg=self.colors['card'],
                        fg=self.colors['text'],
                        font=('Segoe UI', 10, 'bold')).pack(pady=5)
                
                canvas = tk.Canvas(frame, bg=self.colors['accent'],
                                  highlightthickness=0)
                canvas.pack(padx=5, pady=5)
                
                self.display_cv2_image(heatmap, canvas, max_size=250)


def main():
    root = tk.Tk()
    app = ForensicApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
