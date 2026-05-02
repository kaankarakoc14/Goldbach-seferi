# BAŞKENT ÜNİVERSİTESİ
## Özel Ayşeabla Okulları

---

# Proje Özet Formu

---

**Projenin Adı**

Goldbach Seferi: Oyun Tabanlı Goldbach Sanısı Keşif Projesi

**Öğrencinin Adı-Soyadı**

[Buraya adınızı yazınız]

**Öğrencinin Sınıfı**

[Buraya sınıfınızı yazınız]

**Danışman Öğretmen**

[Buraya danışman öğretmen adını yazınız]

---

## Projenin Amacı

Bu projenin amacı, matematikte yaklaşık 280 yıldır çözülememiş ünlü bir problemi araştırmak ve bu problemi eğlenceli bir oyuna dönüştürmektir.

Bu problem **Goldbach Sanısı** olarak bilinir ve şunu söyler: "4'ten büyük her çift sayı, iki asal sayının toplamı olarak yazılabilir." Birkaç örnek vermek gerekirse:

- 10 = 3 + 7
- 20 = 3 + 17 veya 7 + 13
- 30 = 7 + 23 veya 11 + 19 veya 13 + 17
- 100 = 3 + 97 veya 11 + 89 veya 17 + 83 ...

Görüldüğü gibi bazı sayılar tek şekilde, bazıları ise birçok farklı şekilde iki asalın toplamı olarak yazılabiliyor. Bu fikir ilk kez 1742 yılında matematikçi Christian Goldbach tarafından, dönemin en büyük matematikçilerinden Leonhard Euler'e yazdığı bir mektupta ortaya atılmıştır. O günden bu yana bilgisayarlarla trilyonlarca sayı test edilmiş, her seferinde sanı doğru çıkmış, ancak bugüne kadar kesin olarak kanıtlanamamıştır. Bu durum onu matematiğin en ilgi çekici açık problemlerinden biri yapmaktadır.

Projenin iki temel hedefi vardır:

1. **Oyun Tasarımı:** Goldbach Sanısı'nı öğretmek için iki kişilik, stratejik ve eğlenceli bir dijital oyun geliştirmek. Oyunda özel zarlar atılarak bir çift sayı belirlenir ve oyuncular süre bitmeden bu sayıyı iki asal sayının toplamı olarak bulmaya çalışır. Ne kadar çok farklı ayrışım bulunursa o kadar çok puan kazanılır ve altıgen bir oyun tahtasında bölgeler fethedilir.

2. **3D Baskı:** Oyunun fiziksel versiyonunu 3D yazıcı (Bambu Lab A1 Combo) ile tasarlayıp üretmek. Altıgen oyun tahtası, özel zarlar, şövalye figürleri, fetih taşları ve puan sayacı gibi parçalar 3D baskı ile oluşturularak dijital oyunun masa oyunu versiyonunu ortaya koymak.

---

## Projenin İçeriği

Proje üç ana bölümden oluşmaktadır:

### 1. Araştırma

Projenin ilk aşamasında Goldbach Sanısı'nın ne olduğu, tarihçesi ve neden bu kadar önemli olduğu araştırıldı. Christian Goldbach'un 1742'de Euler'e yazdığı mektupta bu fikri ortaya attığı, Euler'in de sanıyı doğru kabul ettiği ancak kanıtlayamadığı öğrenildi.

Araştırma sırasında asal sayı kavramı (yalnızca 1'e ve kendisine bölünebilen sayılar), asal sayıların dağılımı ve Eratosthenes Kalburu yöntemi (belirli bir sayıya kadar tüm asalları bulmak için kullanılan eski ama etkili bir yöntem) incelendi.

Ayrıca Goldbach Sanısı'nın günümüzde bilgisayarlarla 4×10¹⁸'e (4 kentilyon) kadar test edildiği ve hâlâ bir karşı örnek bulunamadığı öğrenildi.

### 2. Oyun Geliştirme (Goldbach Seferi)

HTML, CSS ve JavaScript programlama dilleri kullanarak tarayıcıda çalışan iki kişilik bir strateji oyunu geliştirildi. Oyunun programlama aşamasında yapay zeka destekli kodlama araçlarından yararlanıldı. Oyunun kuralları, mekanikleri, görsel tasarımı ve matematiksel içeriği bizzat planlandı; ardından bu tasarım yapay zeka aracına aktarılarak kodun oluşturulması sağlandı. Üretilen kod incelendi, test edildi ve gerekli düzeltmeler yapıldı. Oyun herhangi bir kurulum gerektirmeden, internet tarayıcısında doğrudan açılarak oynanabilmektedir.

**Oyunun akışı şu şekildedir:**

- Sıradaki oyuncu iki özel zarı atar. Birinci zar (mavi, onlar basamağı) 0, 10, 20, 30, 40 veya 50 değerlerinden birini; ikinci zar (kırmızı, birler basamağı) 0, 2, 4, 6 veya 8 değerlerinden birini verir. İki zarın toplamı her zaman çift bir sayı oluşturur.
- Ekranda hedef çift sayı gösterilir ve 30 saniyelik geri sayım başlar.
- Oyuncu bu süre içinde hedef sayıyı iki asal sayının toplamı olarak yazmaya çalışır. Örneğin hedef 30 ise "7 + 23", "11 + 19" veya "13 + 17" gibi cevaplar girebilir.
- Her doğru ayrışım +10 puan kazandırır. Eğer oyuncu tüm olası ayrışımları bulursa ekstra +15 bonus puan alır. Yanlış cevaplar ise -5 puan kaybettirir (örneğin asal olmayan bir sayı girilirse).
- Her doğru ayrışım aynı zamanda altıgen oyun tahtasında bir bölgenin fethedilmesini sağlar. Fethedilen bölgeler oyuncunun rengiyle (mavi veya kırmızı) boyanır.
- İlk 200 puana ulaşan veya tahtanın yarısından fazlasını fetheden oyuncu oyunu kazanır.

**Oyunun görsel özellikleri:** Uzay temalı animasyonlu arka plan, zırhlı şövalye figürleri, parlama efektli altıgen oyun tahtası, animasyonlu zar atışı ve puan kazanma/kaybetme bildirimleri.

### 3. 3D Baskı Parçaları

Bambu Lab A1 Combo 3D yazıcı ile oyunun fiziksel parçalarının tasarlanması ve basılması planlanmaktadır. Böylece oyun sadece ekranda değil, masa başında da oynanabilecektir.

Hedeflenen parçalar:

| Parça | Açıklama | Renk |
|---|---|---|
| Oyun tahtası | 37 hücreli altıgen grid (~240×240 mm) | Siyah |
| Fetih taşları | Her oyuncu için 20 adet | Mavi ve Kırmızı |
| Onlar zarı | 6 yüzlü (0, 10, 20, 30, 40, 50) | Mavi |
| Birler zarı | 6 yüzlü (0, 2, 4, 6, 8, 0) | Kırmızı |
| Şövalye figürleri | 2 adet savaşçı figürü | Mavi ve Kırmızı |
| Puan sayacı | Kayan göstergeli çubuk | Beyaz |

3D tasarımlar OpenSCAD programı ile parametrik olarak oluşturulacak ve STL formatında Bambu Studio dilimleyicisine aktarılacaktır.

---

## Projenin Sonucu

Projeden beklenen ve şu ana kadar ulaşılan sonuçlar:

1. **Oyun Geliştirme:** "Goldbach Seferi" dijital oyunu tarayıcıda çalışır halde başarıyla geliştirildi. Oyun iki kişilik olarak oynanabiliyor, zar atma, süre sayacı, puan sistemi ve altıgen tahta fethi mekanikleri çalışır durumda. Oyunun sınıf arkadaşlarıyla test edilmesi ve geri bildirim toplanması planlanmaktadır.

2. **Goldbach Sanısı Gözlemi:** Oyun sırasında denenen tüm çift sayıların gerçekten iki asal sayının toplamı olarak yazılabildiğinin görülmesi beklenmektedir. Bu, 280 yıllık sanının doğruluğunun oyuncular tarafından kendi deneyimleriyle gözlemlenmesini sağlayacaktır.

3. **Matematiksel Örüntüler:** Oyun oynanırken bazı örüntülerin fark edilmesi beklenmektedir. Örneğin büyük çift sayıların küçük çift sayılara göre daha fazla farklı ayrışım yoluna sahip olduğu ve 6'nın katı olan sayılarda (6, 12, 18, 24...) ayrışım sayısının komşu çift sayılara göre daha yüksek olduğu gözlemlenebilir.

4. **Eğitsel Etki:** Oyunun, oyuncuların asal sayıları tanıma ve zihinsel toplama hızlarını geliştirmesi beklenmektedir. Ayrıca oyuncuların "her çift sayı gerçekten böyle yazılabilir mi?" sorusunu sorarak matematiksel merak duygusunun artması hedeflenmektedir.

5. **STEAM Yaklaşımı:** Bu proje; matematik (sayılar teorisi, asal sayılar), bilgisayar bilimi (web programlama, algoritma tasarımı), mühendislik (3D modelleme ve baskı) ve sanat (oyun arayüz tasarımı, görsel efektler) alanlarını bir arada kullanmaktadır. Ayrıca proje sürecinde yapay zeka destekli yazılım geliştirme araçları kullanılarak, bu teknolojilerin bir öğrenci tarafından nasıl verimli şekilde yönlendirilebileceği deneyimlenmiştir.

---

## Kaynaklar

1. Goldbach, C. (1742). Goldbach'un Euler'e Mektubu, 7 Haziran 1742.
2. Wang, Y. (2002). *The Goldbach Conjecture.* World Scientific Publishing.
3. Oliveira e Silva, T., Herzog, S., & Pardi, A. (2014). "Empirical verification of the even Goldbach conjecture and computation of prime gaps up to 4×10¹⁸." *Mathematics of Computation*, 83(288), 2033-2060.
4. Weisstein, E. W. "Goldbach Conjecture." *MathWorld.* https://mathworld.wolfram.com/GoldbachConjecture.html
5. Caldwell, C. K. "The Prime Pages." University of Tennessee at Martin. https://primes.utm.edu/
6. 3Dörtgen Blog. "İlköğretim Öğrencileri için 3D Baskı STEM Projesi Fikirleri." https://blog.3dortgen.com/
