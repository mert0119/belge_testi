"""
Sahte Belge Tespit Sistemi - Forgery Detection Module
Görüntü işleme teknikleri ile belge manipülasyonlarını tespit eder.
"""

import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import os
import tempfile


class ELAAnalyzer:
    """
    Error Level Analysis (ELA)
    JPEG sıkıştırma farklarını tespit ederek düzenlenmiş bölgeleri bulur.
    """
    
    def __init__(self, quality=90):
        self.quality = quality
    
    def analyze(self, image_path):
        """
        ELA analizi yapar ve ısı haritası döndürür.
        """
        # Orijinal resmi oku
        original = cv2.imread(image_path)
        if original is None:
            raise ValueError("Resim okunamadı!")
        
        # Geçici JPEG olarak kaydet ve tekrar oku
        temp_path = os.path.join(tempfile.gettempdir(), "ela_temp.jpg")
        cv2.imwrite(temp_path, original, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
        compressed = cv2.imread(temp_path)
        
        # Farkı hesapla
        ela = cv2.absdiff(original, compressed)
        
        # Farkı güçlendir (görünür hale getir)
        ela = ela * 10
        ela = np.clip(ela, 0, 255).astype(np.uint8)
        
        # Gri tonlamaya çevir ve ısı haritası oluştur
        ela_gray = cv2.cvtColor(ela, cv2.COLOR_BGR2GRAY)
        ela_heatmap = cv2.applyColorMap(ela_gray, cv2.COLORMAP_JET)
        
        # Şüphe skoru hesapla (0-100)
        suspicion_score = min(100, (np.mean(ela_gray) / 255) * 500)
        
        # Temizlik
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return ela_heatmap, suspicion_score


class NoiseAnalyzer:
    """
    Gürültü Analizi
    Farklı bölgelerdeki gürültü tutarsızlıklarını tespit eder.
    """
    
    def analyze(self, image_path):
        """
        Gürültü analizi yapar.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Resim okunamadı!")
        
        # Gri tonlamaya çevir
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Laplacian ile kenar/gürültü tespiti
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian = np.absolute(laplacian)
        laplacian = np.uint8(laplacian / laplacian.max() * 255)
        
        # Medyan filtre ile orijinali yumuşat
        blurred = cv2.medianBlur(gray, 5)
        
        # Gürültü = orijinal - yumuşatılmış
        noise = cv2.absdiff(gray, blurred)
        noise = noise * 5  # Güçlendir
        noise = np.clip(noise, 0, 255).astype(np.uint8)
        
        # Isı haritası
        noise_heatmap = cv2.applyColorMap(noise, cv2.COLORMAP_HOT)
        
        # Şüphe skoru
        # Yüksek varyans = tutarsız gürültü = şüpheli
        local_vars = []
        h, w = noise.shape
        block_size = 32
        
        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                block = noise[i:i+block_size, j:j+block_size]
                local_vars.append(np.var(block))
        
        if len(local_vars) > 1:
            variance_of_variances = np.std(local_vars)
            suspicion_score = min(100, variance_of_variances * 2)
        else:
            suspicion_score = 0
        
        return noise_heatmap, suspicion_score


class MetadataAnalyzer:
    """
    EXIF Metadata Analizi
    Düzenleme yazılımı izlerini tespit eder.
    """
    
    # Şüpheli yazılımlar
    SUSPICIOUS_SOFTWARE = [
        'photoshop', 'gimp', 'paint.net', 'photoscape', 
        'lightroom', 'snapseed', 'pixlr', 'fotor',
        'canva', 'picasa', 'affinity', 'corel'
    ]
    
    def analyze(self, image_path):
        """
        Metadata analizi yapar.
        """
        results = {
            'software': None,
            'create_date': None,
            'modify_date': None,
            'camera': None,
            'suspicious': False,
            'details': {}
        }
        
        try:
            img = Image.open(image_path)
            exif_data = img._getexif()
            
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    if tag == 'Software':
                        results['software'] = str(value)
                        # Şüpheli yazılım kontrolü
                        for suspicious in self.SUSPICIOUS_SOFTWARE:
                            if suspicious.lower() in str(value).lower():
                                results['suspicious'] = True
                                break
                    
                    elif tag == 'DateTime':
                        results['modify_date'] = str(value)
                    
                    elif tag == 'DateTimeOriginal':
                        results['create_date'] = str(value)
                    
                    elif tag == 'Make':
                        results['camera'] = str(value)
                    
                    # Tüm detayları kaydet
                    if isinstance(value, (str, int, float)):
                        results['details'][str(tag)] = str(value)
        
        except Exception as e:
            results['error'] = str(e)
        
        # Şüphe skoru
        suspicion_score = 0
        if results['suspicious']:
            suspicion_score += 50
        if results['software'] and not results['camera']:
            suspicion_score += 25  # Kamera bilgisi yok ama yazılım var
        if results['modify_date'] and not results['create_date']:
            suspicion_score += 25  # Orijinal tarih yok
        
        return results, min(100, suspicion_score)


class EdgeAnalyzer:
    """
    Kenar Tutarsızlık Analizi
    Yapıştırılan nesnelerin etrafındaki keskin kenarları tespit eder.
    """
    
    def analyze(self, image_path):
        """
        Kenar analizi yapar.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Resim okunamadı!")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Canny kenar tespiti
        edges = cv2.Canny(gray, 50, 150)
        
        # Kenarları genişlet
        kernel = np.ones((3, 3), np.uint8)
        edges_dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Isı haritası
        edge_heatmap = cv2.applyColorMap(edges_dilated, cv2.COLORMAP_MAGMA)
        
        # Dikdörtgen konturları bul (yapıştırılmış alan olabilir)
        contours, _ = cv2.findContours(edges_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        suspicious_regions = 0
        for contour in contours:
            # Yaklaşık dikdörtgen mi?
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:  # 4 köşe = dikdörtgen
                area = cv2.contourArea(contour)
                if area > 1000:  # Yeterince büyük
                    suspicious_regions += 1
                    cv2.drawContours(edge_heatmap, [approx], -1, (0, 255, 0), 3)
        
        # Şüphe skoru
        suspicion_score = min(100, suspicious_regions * 10)
        
        return edge_heatmap, suspicion_score


class ForensicReport:
    """
    Tüm analizleri birleştirir ve genel bir rapor üretir.
    """
    
    def __init__(self):
        self.ela = ELAAnalyzer()
        self.noise = NoiseAnalyzer()
        self.metadata = MetadataAnalyzer()
        self.edge = EdgeAnalyzer()
    
    def full_analysis(self, image_path):
        """
        Tam analiz yapar ve sonuçları döndürür.
        """
        results = {}
        
        # ELA
        try:
            ela_map, ela_score = self.ela.analyze(image_path)
            results['ela'] = {'heatmap': ela_map, 'score': ela_score}
        except Exception as e:
            results['ela'] = {'error': str(e), 'score': 0}
        
        # Noise
        try:
            noise_map, noise_score = self.noise.analyze(image_path)
            results['noise'] = {'heatmap': noise_map, 'score': noise_score}
        except Exception as e:
            results['noise'] = {'error': str(e), 'score': 0}
        
        # Metadata
        try:
            meta_info, meta_score = self.metadata.analyze(image_path)
            results['metadata'] = {'info': meta_info, 'score': meta_score}
        except Exception as e:
            results['metadata'] = {'error': str(e), 'score': 0}
        
        # Edge
        try:
            edge_map, edge_score = self.edge.analyze(image_path)
            results['edge'] = {'heatmap': edge_map, 'score': edge_score}
        except Exception as e:
            results['edge'] = {'error': str(e), 'score': 0}
        
        # Genel skor (ağırlıklı ortalama)
        weights = {'ela': 0.35, 'noise': 0.25, 'metadata': 0.20, 'edge': 0.20}
        total_score = 0
        for key, weight in weights.items():
            if 'score' in results[key]:
                total_score += results[key]['score'] * weight
        
        results['overall_score'] = round(total_score, 1)
        results['verdict'] = self._get_verdict(total_score)
        
        return results
    
    def _get_verdict(self, score):
        """
        Skora göre karar verir.
        """
        if score < 20:
            return "✅ GÜVENILIR - Manipülasyon izi bulunamadı"
        elif score < 40:
            return "⚠️ DÜŞÜK RİSK - Hafif şüpheli bölgeler var"
        elif score < 60:
            return "⚠️ ORTA RİSK - Şüpheli düzenlemeler tespit edildi"
        elif score < 80:
            return "🚨 YÜKSEK RİSK - Ciddi manipülasyon izleri var"
        else:
            return "🚨 ÇOK YÜKSEK RİSK - Belge muhtemelen sahte!"
