<div align="center">

#  PRNU Kamera Parmak İzi Analizi

### PRNU, PCE ve EXIF verileriyle kamera kaynak doğrulaması

Şüpheli bir fotoğrafın belirli bir kamera veya akıllı telefondan çekilip çekilmediğini deneysel olarak analiz eden Python tabanlı masaüstü uygulaması.

<br>

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Görüntü%20İşleme-green?logo=opencv)](https://opencv.org/)
[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-yellow.svg)](LICENSE)
[![Durum](https://img.shields.io/badge/Durum-Deneysel-orange)](#adli-kullanım-uyarısı)

[English](README.md) · [Türkçe](README_TR.md)

</div>

---

## Genel Bakış

**PRNU Kamera Parmak İzi Analizi**, dijital görüntü adli bilişimi alanında aşağıdaki soruyu araştırmak amacıyla geliştirilmiş deneysel bir uygulamadır:

> Bu fotoğraf gerçekten iddia edilen kamera veya akıllı telefonla mı çekildi?

Uygulama, bir cihazdan alınan referans fotoğrafları kullanarak sensör parmak izi oluşturur. Daha sonra şüpheli fotoğraftan çıkarılan gürültü deseni bu referans parmak iziyle karşılaştırılır.

Sistem iki analiz katmanını birlikte kullanır:

* **Optik analiz:** PRNU sensör parmak izinin PCE metriğiyle karşılaştırılması
* **Metadata analizi:** EXIF marka, model, yazılım ve görüntü bilgilerinin karşılaştırılması

> [!WARNING]
> Bu proje eğitim, araştırma ve deneysel analiz amacıyla geliştirilmiştir. Üretilen sonuçlar tek başına kesin adli delil veya hukuki karar olarak değerlendirilmemelidir.

## Temel Özellikler

* PRNU tabanlı kamera sensörü parmak izi çıkarma
* RGB çok kanallı gürültü işleme
* Daubechies db8 Wavelet Denoising
* Fourier tabanlı yapaylık temizleme
* Peak-to-Correlation Energy hesaplama
* Pearson korelasyon hesaplama
* EXIF metadata karşılaştırması
* JPEG sıkıştırma ve kalite uyarıları
* HEIC görüntü desteği
* Apple cihazlar için adaptif analiz eşiği
* Oluşturulan parmak izlerini kaydetme ve yükleme
* TXT formatında analiz raporu oluşturma
* Tkinter tabanlı grafik kullanıcı arayüzü

## Uygulamanın Çalışma Akışı

```text
Referans fotoğraflar
        │
        ▼
Gürültü kalıntılarının çıkarılması
        │
        ▼
Referans PRNU parmak izi
        │
        ├──────────────────┐
        ▼                  ▼
Şüpheli fotoğraf       EXIF metadata
        │                  │
        ▼                  ▼
 PCE karşılaştırması   Model karşılaştırması
        │                  │
        └────────┬─────────┘
                 ▼
          Deneysel sonuç
```

## Kurulum

Projeyi bilgisayarınıza klonlayın:

```bash
git clone https://github.com/erenkocak1/prnu-camera-fingerprint-analysis.git
```

Proje klasörüne girin:

```bash
cd prnu-camera-fingerprint-analysis
```

Gerekli Python paketlerini yükleyin:

```bash
pip install -r requirements.txt
```

Uygulamayı çalıştırın:

```bash
python prnu_v4.py
```

Bazı sistemlerde aşağıdaki komut gerekebilir:

```bash
python3 prnu_v4.py
```

## Temel Kullanım

1. Referans cihazla çekilmiş yaklaşık **25–50 adet orijinal fotoğraf** hazırlayın.
2. Parmak izi oluşturmak için **Referans Klasörü Seç & İşle** butonuna basın.
3. Oluşturulan veya daha önce kaydedilmiş referans parmak izini yükleyin.
4. **Şüpheli Fotoğrafı Seç ve Analiz Et** butonuna basın.
5. PCE, Pearson, EXIF ve görüntü kalitesi sonuçlarını inceleyin.
6. Gerekli durumlarda TXT formatında analiz raporu oluşturun.

> [!IMPORTANT]
> WhatsApp, Instagram veya benzeri platformlardan aktarılan görüntüler yeniden boyutlandırılabilir, sıkıştırılabilir veya EXIF verilerinden arındırılabilir. Mümkün olduğunca doğrudan cihazdan alınan orijinal dosyalar kullanılmalıdır.

## Referans Fotoğraf Önerileri

Daha güvenilir bir parmak izi oluşturmak için referans fotoğrafların:

* Doğrudan orijinal cihazdan alınması
* Farklı sahneler ve ışık koşulları içermesi
* Orijinal çözünürlüğünü koruması
* Sosyal medya platformlarından geçirilmemesi
* Aşırı karanlık veya tamamen tek renk olmaması
* Ekran görüntüsü olmaması
* Filtrelenmemiş ve düzenlenmemiş olması

önerilir.

## Karar Eşikleri

Normal analiz modunda kullanılan varsayılan PCE eşikleri:

|     PCE değeri | Deneysel yorum      |
| -------------: | ------------------- |
| 20'nin altında | Negatif             |
|          20–59 | Belirsiz veya zayıf |
| 60 ve üzerinde | Güçlü korelasyon    |

Referans cihazın Apple ürünü olduğu tespit edilirse program mevcut durumda deneysel olarak `30` değerinde adaptif eşik kullanır.

Bu değerler uygulamaya ait deneysel karar eşikleridir. Evrensel veya bilimsel olarak doğrulanmış adli eşikler değildir.

<details>
<summary><strong>Teknik analiz ayrıntıları</strong></summary>

### PRNU Analizi

Kamera sensörlerinin piksel hücrelerinde üretim aşamasında mikroskobik ışık duyarlılığı farklılıkları oluşabilir.

Bu farklılıklar, fotoğraflara görünmez bir gürültü deseni olarak yansır. Bu desen, kamera sensörünün optik parmak izi olarak değerlendirilebilir.

### RGB Çok Kanallı İşleme

Fotoğrafın kırmızı, yeşil ve mavi kanalları ayrı ayrı işlenir.

Bayer sensör düzenlerinde yeşil piksel sayısı genellikle kırmızı ve mavi piksel sayısından fazla olduğu için yeşil kanala ek ağırlık verilir.

Bu yöntem, fotoğrafı doğrudan gri tona dönüştürmeye göre daha fazla sensör bilgisinin korunmasını amaçlar.

### Wavelet Denoising

Görüntü içeriğini ve yüksek frekanslı gürültü bileşenlerini ayırmak için Daubechies db8 Wavelet yöntemi kullanılır.

Temizlenmiş görüntü orijinal görüntüden çıkarılarak sensör gürültüsü kalıntısı tahmin edilir.

### Benzersiz Olmayan Yapaylıkların Temizlenmesi

Çıkarılan gürültü kalıntısı yalnızca PRNU sinyalini içermeyebilir.

Aşağıdaki ortak yapılar farklı cihazlarda benzerlik oluşturabilir:

* JPEG blok desenleri
* Satır ve sütun bant izleri
* Ortak görüntü sinyal işlemcisi yapaylıkları
* Lens kaynaklı desenler
* Periyodik görüntü işleme yapıları

Uygulama, karşılaştırmadan önce bu ortak yapıların etkisini azaltmaya çalışır.

### Fourier Filtreleme

Periyodik sensör çizgileri, lens kaynaklı yapaylıklar ve bazı ortak frekans bileşenleri Fourier frekans alanında tespit edilerek filtrelenir.

Bu işlem, farklı cihazlar arasında oluşabilecek yanlış benzerlikleri azaltmayı amaçlar.

### PCE Karşılaştırması

Peak-to-Correlation Energy, kayıtlı referans parmak iziyle şüpheli fotoğraftan çıkarılan gürültü kalıntısı arasındaki benzerliği ölçer.

Daha yüksek PCE değeri genellikle daha güçlü korelasyon anlamına gelir.

Ancak yüksek bir PCE değeri tek başına iki fotoğrafın kesin olarak aynı fiziksel cihazdan geldiğini kanıtlamaz.

### Pearson Korelasyonu

Pearson korelasyonu ek bir referans değeri olarak hesaplanır.

PCE değeriyle birlikte arayüzde gösterilir ancak temel karar metriği olarak kullanılmaz.

### EXIF Karşılaştırması

Uygulama, mevcut olması durumunda aşağıdaki metadata alanlarını karşılaştırır:

* Cihaz üreticisi
* Cihaz modeli
* Kullanılan yazılım
* Görüntü çözünürlüğü
* Çekim tarihi
* Kamera ayarları
* Diğer EXIF alanları

Optik sensör analiziyle EXIF karşılaştırmasının birlikte kullanılması, yalnızca tek bir analiz yöntemine dayanmaktan daha kapsamlı bir değerlendirme sağlar.

</details>

<details>
<summary><strong>Apple adaptif analiz modu</strong></summary>

Apple cihazlar fotoğraf oluşturma sırasında aşağıdaki bilişimsel fotoğrafçılık işlemlerini uygulayabilir:

* Smart HDR
* Deep Fusion
* Neural Engine işlemleri
* Gürültü azaltma
* Çoklu kare birleştirme

Bu işlemler PRNU sinyalini zayıflatabilir veya baskılayabilir.

Referans cihazın EXIF bilgilerinde Apple cihazı olduğu tespit edildiğinde uygulama otomatik olarak daha düşük bir PCE eşik değeri kullanır.

Bu davranış deneysel olarak uygulanmıştır ve bütün Apple modellerinde doğru sonuç garantisi vermez.

</details>

<details>
<summary><strong>Desteklenen formatlar ve oluşturulan dosyalar</strong></summary>

### Desteklenen Dosya Formatları

* JPG
* JPEG
* PNG
* HEIC
* WEBP

HEIC dosyalarını açmak için `pillow-heif` paketi kullanılmaktadır.

### Oluşturulan Dosyalar

Sensör parmak izleri aşağıdaki yapıda saklanır:

```text
parmak_izleri/
├── fp_CIHAZ_MODELI.npy
└── meta_CIHAZ_MODELI.json
```

`.npy` dosyası oluşturulan sensör parmak izini içerir.

`.json` dosyası ise referans cihazın metadata bilgilerini, kullanılan fotoğraf sayısını ve ek işleme bilgilerini içerebilir.

Bu dosyalarda cihaza veya kullanıcıya ait bilgiler bulunabileceği için herkese açık repolara yüklenmemelidir.

</details>

## Sosyal Medya ve JPEG Sıkıştırması

WhatsApp, Instagram, Facebook ve Telegram gibi platformlar görüntüleri yeniden boyutlandırabilir veya sıkıştırabilir.

Bu işlemler:

* PRNU sinyalini zayıflatabilir
* EXIF metadata bilgilerini silebilir
* PCE değerini düşürebilir
* Yanlış negatif sonuçlar oluşturabilir
* Fotoğrafa ek sıkıştırma yapaylıkları ekleyebilir

Bu nedenle analizlerde mümkün olduğunca orijinal görüntü dosyaları kullanılmalıdır.

## Analiz Raporu

Bir fotoğraf analiz edildikten sonra uygulama TXT formatında rapor oluşturabilir.

Oluşturulan raporda aşağıdaki bilgiler bulunabilir:

* Analiz tarihi ve saati
* PCE skoru
* Pearson korelasyonu
* Kullanılan eşik değerleri
* Referans fotoğraf sayısı
* Tahmini JPEG kalitesi
* Sıkıştırma uyarıları
* Referans cihaz modeli
* Şüpheli fotoğraf cihaz modeli
* Nihai deneysel karar
* Ayrıntılı EXIF karşılaştırması

Rapor, deneysel sonuçların belgelenmesi amacıyla hazırlanır.

## Proje Yapısı

```text
prnu-camera-fingerprint-analysis/
├── prnu_v4.py
├── requirements.txt
├── README.md
├── README_TR.md
└── .gitignore
```

`parmak_izleri` klasörü uygulama ilk kez çalıştırıldığında otomatik olarak oluşturulur.

## Bilinen Sınırlamalar

* Aynı marka ve modeldeki farklı telefonların EXIF model bilgileri aynı olabilir.
* Aynı sensörü veya görüntü işleme altyapısını kullanan farklı cihazlarda ortak yapaylıklar oluşabilir.
* EXIF metadata bilgileri silinebilir, değiştirilebilir veya sahte olarak oluşturulabilir.
* Sosyal medya sıkıştırması PRNU sinyalini önemli ölçüde bozabilir.
* Ekran görüntüleri kamera sensörü parmak izi analizi için uygun değildir.
* Kırpılmış, yeniden boyutlandırılmış veya yeniden sıkıştırılmış görüntüler güvenilir olmayan sonuçlar üretebilir.
* Bilişimsel fotoğrafçılık işlemleri PRNU sinyalini baskılayabilir.
* Aynı eşik değerleri her cihazda eşit başarı sağlamayabilir.
* Yüksek PCE değeri tek başına iki görüntünün aynı fiziksel cihazdan geldiğini kanıtlamaz.
* Yanlış pozitif ve yanlış negatif sonuçlar oluşabilir.
* Uygulama geniş ve kontrollü bir adli veri seti üzerinde doğrulanmamıştır.
* Bu uygulama sertifikalı veya ticari bir adli inceleme aracı değildir.

## Gizlilik

Referans ve şüpheli fotoğraflar aşağıdaki kişisel bilgileri içerebilir:

* Konum bilgileri
* Cihaz modeli
* Çekim tarihi
* Kamera ayarları
* Kullanılan yazılım
* Diğer EXIF metadata alanları

Herkese açık GitHub reposuna aşağıdaki dosyaları yüklemeyin:

```text
Özel referans fotoğrafları
Şüpheli fotoğraflar
Oluşturulan .npy parmak izleri
Metadata içeren JSON dosyaları
Kişisel bilgi içeren analiz raporları
```

## Önerilen `.gitignore`

```gitignore
__pycache__/
*.py[cod]

.venv/
venv/

parmak_izleri/
*.npy

*.log
.DS_Store
Thumbs.db
```

Bütün `.json` dosyalarını genel olarak engellemek önerilmez. Projeye daha sonra yapılandırma dosyaları eklenebilir.

Mevcut metadata dosyaları `parmak_izleri/` klasöründe oluşturulduğu için bu klasörün engellenmesi yeterlidir.

## Geliştirme Planı

* Projenin modüler dosya yapısına ayrılması
* İlerleme göstergesi eklenmesi
* Uzun işlemleri iptal etme desteği
* Çoklu şüpheli fotoğraf analizi
* CSV ve PDF rapor çıktısı
* PCE dağılım grafiklerinin oluşturulması
* Otomatik testlerin eklenmesi
* Cihaza özel eşik kalibrasyonu
* Kontrollü karşılaştırma veri seti
* ROC eğrisi hesaplama
* Yanlış pozitif ve yanlış negatif oranlarının ölçülmesi
* Komut satırı arayüzü
* Tekrarlanabilir deney ve karşılaştırma altyapısı

## Katkıda Bulunma

Projeyi fork ederek geliştirmeler yapabilir ve pull request gönderebilirsiniz.

Bir hata bildirirken aşağıdaki bilgilerin paylaşılması faydalı olacaktır:

* İşletim sistemi
* Python sürümü
* Kullanılan görüntü formatı
* Tam hata mesajı
* Hatanın oluştuğu işlem
* Mümkünse kişisel bilgi içermeyen örnek bir senaryo

Herkese açık issue kayıtlarına kişisel veya hassas metadata içeren fotoğraflar yüklemeyin.

## Adli Kullanım Uyarısı

Bu yazılım eğitim, araştırma ve deneysel analiz amacıyla sunulmaktadır.

Uygulamanın ürettiği sonuçlar tek başına kesin adli delil, bilirkişi görüşü veya hukuki sonuç olarak kullanılmamalıdır.

Gerçek bir adli incelemede ayrıca aşağıdaki unsurlar değerlendirilmelidir:

* Orijinal dosyanın bütünlüğü
* Kriptografik hash değerleri
* Delil zinciri
* Cihaz edinim yöntemi
* Tekrarlanabilir testler
* Kontrollü veri setleri
* Bilinen hata oranları
* Doğrulama prosedürleri
* Bağımsız uzman incelemesi
* Alternatif açıklamalar

Nihai değerlendirme, diğer adli bulgular ve uzman görüşleriyle birlikte yapılmalıdır.

## Geliştirici

**Yusuf Eren Koçak**

[GitHub Profili](https://github.com/erenkocak1)

## Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında yayımlanmaktadır.

---

Bu proje; kamera sensörü parmak izi analizi, dijital görüntü adli bilişimi ve kaynak kamera tanımlama alanlarında eğitim ve araştırma amacıyla geliştirilmiştir.
