[English Version](README_EN.md)

PRNU Camera Fingerprint Analysis

PRNU, PCE ve EXIF verilerini kullanarak bir fotoğrafın belirli bir kamera veya telefon tarafından çekilip çekilmediğini analiz eden masaüstü uygulaması.

Bu proje, kamera sensörlerinde üretim aşamasında oluşan benzersiz gürültü desenlerini kullanarak cihaz doğrulaması gerçekleştirmeyi amaçlamaktadır. Sistem, yalnızca sensör parmak izini değil, fotoğrafın EXIF metadata bilgilerini de değerlendirerek daha kapsamlı bir sonuç üretir.

Projenin Amacı

Temel olarak aşağıdaki soruya cevap vermeyi hedefler:

Bu fotoğraf gerçekten iddia edilen cihazdan mı çekildi?

Program, şüpheli cihazdan alınan referans fotoğraflar üzerinden bir sensör parmak izi oluşturur. Daha sonra analiz edilmek istenen fotoğrafın gürültü deseni bu parmak iziyle karşılaştırılır.

Özellikler
PRNU tabanlı kamera sensörü parmak izi çıkarma
RGB çok kanallı gürültü analizi
Daubechies db8 Wavelet Denoising
Fourier tabanlı periyodik gürültü temizleme
PCE hesaplama
Pearson korelasyon değeri
EXIF metadata analizi
Referans ve şüpheli fotoğraf metadata karşılaştırması
JPEG sıkıştırma ve kalite kontrolü
HEIC fotoğraf desteği
Apple cihazları için adaptif PCE eşik sistemi
Oluşturulan sensör parmak izlerini kaydetme ve tekrar yükleme
TXT formatında inceleme raporu oluşturma
Tkinter tabanlı grafik arayüz
Kullanılan Teknolojiler
Python
OpenCV
NumPy
PyWavelets
Pillow
Pillow-HEIF
Tkinter
Kurulum

Projeyi bilgisayarınıza indirin:

git clone https://github.com/erenkocak1/prnu-camera-fingerprint-analysis.git

Proje klasörüne girin:

cd prnu-camera-fingerprint-analysis

Gerekli Python kütüphanelerini yükleyin:

pip install -r requirements.txt

Programı çalıştırın:

python prnu_v4.py

Bazı sistemlerde aşağıdaki komutun kullanılması gerekebilir:

python3 prnu_v4.py
Kullanım
1. Referans Fotoğrafları Hazırlama

Analiz edilecek cihazla çekilmiş yaklaşık 25-50 adet fotoğrafı aynı klasöre yerleştirin.

Daha iyi sonuç elde etmek için:

Fotoğrafların doğrudan cihaz kamerasından alınması
WhatsApp, Instagram veya benzeri platformlardan geçirilmemesi
Orijinal çözünürlüklerinin korunması
Farklı sahneler ve ışık koşullarında çekilmesi
Aşırı karanlık veya tamamen düz görüntüler kullanılmaması

önerilir.

2. Sensör Parmak İzi Oluşturma

Programı açtıktan sonra:

Referans Klasörü Seç & İşle butonuna basın.
Referans fotoğrafların bulunduğu klasörü seçin.
Fotoğrafların işlenmesini bekleyin.
Oluşturulan sensör parmak izi otomatik olarak kaydedilir.

Kaydedilen parmak izleri parmak_izleri klasöründe saklanır.

3. Şüpheli Fotoğrafı Analiz Etme
Bir referans parmak izi oluşturun veya daha önce oluşturulmuş bir parmak izini yükleyin.
Şüpheli Fotoğrafı Seç ve Analiz Et butonuna basın.
Analiz edilmek istenen fotoğrafı seçin.
Program PCE, Pearson, EXIF ve görüntü kalitesi sonuçlarını gösterir.
Karar Sistemi

Normal modda varsayılan PCE eşikleri:

PCE Değeri	Sonuç
PCE < 20	Negatif
20 ≤ PCE < 60	Şüpheli / Belirsiz
PCE ≥ 60	Güçlü eşleşme

Apple cihazlarında, görüntü işleme algoritmalarının PRNU sinyalini baskılayabilmesi nedeniyle sistem daha düşük bir adaptif eşik kullanabilir.

Varsayılan Apple eşleşme eşiği:

PCE ≥ 30

Eşik değerleri program arayüzü üzerinden değiştirilebilir.

Analiz Katmanları
PRNU Analizi

Kamera sensörlerinde üretim sırasında oluşan mikroskobik ışık duyarlılığı farklılıkları, fotoğraflarda görünmeyen bir gürültü deseni oluşturur.

Bu desen, kamera sensörünün optik parmak izi olarak değerlendirilebilir.

Wavelet Denoising

Fotoğraf, Daubechies db8 Wavelet yöntemiyle ayrıştırılır. Görüntünün temel içeriği ile gürültü bileşenleri birbirinden ayrılmaya çalışılır.

Temizlenmiş görüntünün orijinal görüntüden çıkarılmasıyla sensör gürültüsü elde edilir.

Fourier Temizleme

Periyodik sensör çizgileri, JPEG blok izleri ve lens kaynaklı bazı ortak yapılar Fourier frekans alanında filtrelenir.

Bu işlem, farklı cihazlarda ortak olarak bulunabilecek yapay benzerlikleri azaltmayı amaçlar.

PCE

Peak to Correlation Energy, referans parmak iziyle test görüntüsünden çıkarılan gürültü arasındaki benzerliğin ölçülmesinde kullanılır.

Yüksek PCE değeri daha güçlü bir korelasyon anlamına gelir. Ancak PCE değeri tek başına kesin bir adli kanıt olarak değerlendirilmemelidir.

EXIF Analizi

Program aşağıdakiler dahil olmak üzere fotoğraf metadata alanlarını karşılaştırır:

Make
Model
Software
Görüntü çözünürlüğü
Çekim tarihi
Kamera bilgileri
Diğer EXIF alanları

Optik sensör izi ile EXIF bilgisinin birlikte değerlendirilmesi, yalnızca tek bir yöntemin kullanılmasına göre daha kapsamlı bir analiz sağlar.

JPEG ve Sosyal Medya Sıkıştırması

WhatsApp, Instagram, Facebook ve Telegram gibi platformlar görüntüleri yeniden boyutlandırabilir veya sıkıştırabilir.

Bu işlemler:

PRNU sinyalini zayıflatabilir
EXIF bilgilerini silebilir
PCE değerini düşürebilir
Yanlış negatif sonuçlara neden olabilir

Bu nedenle mümkün olduğunca orijinal fotoğraflar kullanılmalıdır.

Desteklenen Dosya Formatları
JPG
JPEG
PNG
HEIC
WEBP

HEIC dosyalarının açılması için pillow-heif kütüphanesi kullanılmaktadır.

Oluşturulan Dosyalar

Program tarafından oluşturulan sensör parmak izleri aşağıdaki yapıda kaydedilir:

parmak_izleri/
├── fp_CIHAZ_MODELI.npy
└── meta_CIHAZ_MODELI.json

.npy dosyası sensör parmak izini, .json dosyası ise referans cihaz metadata bilgilerini içerir.

Bu dosyalarda cihaz bilgileri bulunabileceği için herkese açık ortamlarda paylaşılmadan önce içerikleri kontrol edilmelidir.

Proje Yapısı
prnu-camera-fingerprint-analysis/
├── prnu_v4.py
├── requirements.txt
├── README.md
├── .gitignore
└── parmak_izleri/

parmak_izleri klasörü program ilk çalıştırıldığında otomatik olarak oluşturulabilir.

Bilinen Sınırlamalar
Aynı marka ve modeldeki farklı telefonların EXIF bilgileri aynı olabilir.
Aynı sensör veya görüntü işleme altyapısını kullanan farklı cihazlar yüksek benzerlik üretebilir.
Sosyal medya sıkıştırması PRNU sinyalini bozabilir.
Ekran görüntüleri sensör parmak izi analizi için uygun değildir.
Düzenlenmiş, yeniden boyutlandırılmış veya filtre uygulanmış fotoğraflar güvenilir sonuç vermeyebilir.
Apple cihazlarının görüntü işleme sistemleri PRNU sinyalini önemli ölçüde baskılayabilir.
Kullanılan eşik değerleri her cihaz ve veri seti için aynı başarıyı garanti etmez.
Bu proje bilimsel veya adli olarak doğrulanmış ticari bir bilirkişi yazılımı değildir.
Adli Kullanım Uyarısı

Bu proje eğitim, araştırma ve deneysel analiz amacıyla geliştirilmiştir.

Programın ürettiği sonuçlar tek başına kesin adli delil, bilirkişi görüşü veya hukuki karar olarak kullanılmamalıdır. Gerçek bir adli incelemede:

Orijinal dosya bütünlüğü
Hash değerleri
Delil zinciri
Cihaz edinim yöntemi
Tekrarlanabilir testler
Kontrollü veri setleri
Hata oranları
Uzman değerlendirmesi

gibi unsurlar ayrıca dikkate alınmalıdır.

Gizlilik

Referans ve şüpheli fotoğraflar aşağıdaki kişisel bilgileri içerebilir:

Konum bilgileri
Cihaz modeli
Çekim tarihi
Kullanılan yazılım
Kamera ayarları
Diğer EXIF metadata alanları

Testlerde kullanılan özel fotoğrafları veya oluşturulan metadata dosyalarını herkese açık GitHub reposuna yüklemeyin.

Geliştirme Fikirleri
PDF formatında rapor oluşturma
Çoklu şüpheli fotoğraf analizi
Test sonuçlarını CSV olarak dışa aktarma
PCE dağılım grafikleri
Referans veri seti kalite kontrolü
Cihaz başına kalibre edilmiş eşik sistemi
ROC eğrisi ve hata oranı hesaplama
Otomatik test sistemi
Komut satırı arayüzü
Daha modüler proje yapısı
Aynı model farklı cihaz testlerinin genişletilmesi
Katkıda Bulunma

Projeyi fork ederek geliştirmeler yapabilir ve pull request gönderebilirsiniz.

Hata bildirirken aşağıdaki bilgileri paylaşmanız faydalı olacaktır:

İşletim sistemi
Python sürümü
Kullanılan görüntü formatı
Hata mesajı
Hatanın oluştuğu işlem
Mümkünse kişisel veri içermeyen örnek senaryo
Lisans

Bu proje için henüz bir lisans tanımlanmamıştır.

Lisans eklenene kadar kaynak kodun kullanım, dağıtım ve değiştirme koşulları açık şekilde tanımlanmış değildir.

Geliştirici

Yusuf Eren Koçak

GitHub: erenkocak1

Bu proje, kamera sensörü parmak izi analizi ve dijital görüntü adli bilişimi alanlarında eğitim ve araştırma amacıyla geliştirilmiştir.
