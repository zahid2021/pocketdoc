import json
import urllib.parse
import urllib.request

# name, kind, division, district, lat, lng
_RAW = """
Lahore|division|Lahore|Lahore|31.5204|74.3587
Gujranwala|division|Gujranwala|Gujranwala|32.1877|74.1945
Faisalabad|division|Faisalabad|Faisalabad|31.4504|73.1350
Rawalpindi|division|Rawalpindi|Rawalpindi|33.5651|73.0169
Sargodha|division|Sargodha|Sargodha|32.0836|72.6711
Multan|division|Multan|Multan|30.1575|71.5249
Bahawalpur|division|Bahawalpur|Bahawalpur|29.3956|71.6836
Dera Ghazi Khan|division|Dera Ghazi Khan|Dera Ghazi Khan|30.0561|70.6348
Sahiwal|division|Sahiwal|Sahiwal|30.6682|73.1114
Lahore|district|Lahore|Lahore|31.5204|74.3587
Kasur|district|Lahore|Kasur|31.1170|74.4490
Nankana Sahib|district|Lahore|Nankana Sahib|31.4492|73.7060
Sheikhupura|district|Lahore|Sheikhupura|31.7167|73.9850
Gujranwala|district|Gujranwala|Gujranwala|32.1877|74.1945
Gujrat|district|Gujranwala|Gujrat|32.5742|74.0754
Hafizabad|district|Gujranwala|Hafizabad|32.0709|73.6880
Mandi Bahauddin|district|Gujranwala|Mandi Bahauddin|32.5830|73.4840
Narowal|district|Gujranwala|Narowal|32.1017|74.8730
Sialkot|district|Gujranwala|Sialkot|32.4945|74.5229
Wazirabad|district|Gujranwala|Wazirabad|32.4430|74.1160
Faisalabad|district|Faisalabad|Faisalabad|31.4504|73.1350
Chiniot|district|Faisalabad|Chiniot|31.7200|72.9789
Jhang|district|Faisalabad|Jhang|31.2681|72.3186
Toba Tek Singh|district|Faisalabad|Toba Tek Singh|30.9709|72.4827
Rawalpindi|district|Rawalpindi|Rawalpindi|33.5651|73.0169
Attock|district|Rawalpindi|Attock|33.7660|72.3600
Chakwal|district|Rawalpindi|Chakwal|32.9328|72.8556
Jhelum|district|Rawalpindi|Jhelum|32.9425|73.7257
Talagang|district|Rawalpindi|Talagang|32.9274|72.4156
Sargodha|district|Sargodha|Sargodha|32.0836|72.6711
Khushab|district|Sargodha|Khushab|32.2967|72.3525
Mianwali|district|Sargodha|Mianwali|32.5839|71.5436
Bhakkar|district|Sargodha|Bhakkar|31.6250|71.0653
Multan|district|Multan|Multan|30.1575|71.5249
Khanewal|district|Multan|Khanewal|30.3017|71.9321
Lodhran|district|Multan|Lodhran|29.5330|71.6330
Vehari|district|Multan|Vehari|30.0452|72.3489
Bahawalpur|district|Bahawalpur|Bahawalpur|29.3956|71.6836
Bahawalnagar|district|Bahawalpur|Bahawalnagar|29.9983|73.2536
Rahim Yar Khan|district|Bahawalpur|Rahim Yar Khan|28.4212|70.2989
Dera Ghazi Khan|district|Dera Ghazi Khan|Dera Ghazi Khan|30.0561|70.6348
Layyah|district|Dera Ghazi Khan|Layyah|30.9693|70.9428
Muzaffargarh|district|Dera Ghazi Khan|Muzaffargarh|30.0703|71.1933
Rajanpur|district|Dera Ghazi Khan|Rajanpur|29.1041|70.3297
Taunsa|district|Dera Ghazi Khan|Taunsa|30.7040|70.6570
Sahiwal|district|Sahiwal|Sahiwal|30.6682|73.1114
Okara|district|Sahiwal|Okara|30.8138|73.4534
Pakpattan|district|Sahiwal|Pakpattan|30.3430|73.3920
Model Town|town|Lahore|Lahore|31.4830|74.3160
Johar Town|town|Lahore|Lahore|31.4697|74.2728
Gulberg|town|Lahore|Lahore|31.5206|74.3486
Shahdara|town|Lahore|Lahore|31.6220|74.2860
Raiwind|town|Lahore|Lahore|31.2480|74.2160
Cantt Lahore|town|Lahore|Lahore|31.5200|74.3900
Chunian|tehsil|Lahore|Kasur|30.9640|73.9790
Pattoki|tehsil|Lahore|Kasur|31.0210|73.8530
Kot Radha Kishan|tehsil|Lahore|Kasur|31.1710|74.1000
Ferozewala|tehsil|Lahore|Sheikhupura|31.6390|74.2590
Muridke|tehsil|Lahore|Sheikhupura|31.8020|74.2570
Safdarabad|tehsil|Lahore|Sheikhupura|31.7160|73.5660
Sharaqpur|tehsil|Lahore|Sheikhupura|31.4630|74.1000
Shahkot|tehsil|Lahore|Nankana Sahib|31.5700|73.4850
Sangla Hill|tehsil|Lahore|Nankana Sahib|31.7160|73.3830
Kamoke|tehsil|Gujranwala|Gujranwala|31.9750|74.2240
Nowshera Virkan|tehsil|Gujranwala|Gujranwala|31.9650|73.9710
Kharian|tehsil|Gujranwala|Gujrat|32.8110|73.8650
Lalamusa|town|Gujranwala|Gujrat|32.7010|73.9570
Jalalpur Jattan|tehsil|Gujranwala|Gujrat|32.6420|74.2060
Sarai Alamgir|tehsil|Gujranwala|Gujrat|32.9040|73.7550
Daska|tehsil|Gujranwala|Sialkot|32.3240|74.3500
Pasrur|tehsil|Gujranwala|Sialkot|32.2680|74.6670
Sambrial|tehsil|Gujranwala|Sialkot|32.4780|74.3530
Shakargarh|tehsil|Gujranwala|Narowal|32.2640|75.1600
Zafarwal|tehsil|Gujranwala|Narowal|32.3460|74.8990
Pindi Bhattian|tehsil|Gujranwala|Hafizabad|31.8980|73.2730
Phalia|tehsil|Gujranwala|Mandi Bahauddin|32.4310|73.5770
Malakwal|tehsil|Gujranwala|Mandi Bahauddin|32.5550|73.2120
Jaranwala|tehsil|Faisalabad|Faisalabad|31.3340|73.4190
Samundri|tehsil|Faisalabad|Faisalabad|31.0630|72.9610
Tandlianwala|tehsil|Faisalabad|Faisalabad|31.0330|73.1330
Chak Jhumra|tehsil|Faisalabad|Faisalabad|31.5680|73.1830
Gojra|tehsil|Faisalabad|Toba Tek Singh|31.1490|72.6860
Kamalia|tehsil|Faisalabad|Toba Tek Singh|30.7270|72.6460
Shorkot|tehsil|Faisalabad|Jhang|30.8380|72.1020
Lalian|tehsil|Faisalabad|Chiniot|31.8240|72.8000
Bhowana|tehsil|Faisalabad|Chiniot|31.5680|72.6490
Gujar Khan|tehsil|Rawalpindi|Rawalpindi|33.2540|73.3040
Kahuta|tehsil|Rawalpindi|Rawalpindi|33.5880|73.3880
Taxila|tehsil|Rawalpindi|Rawalpindi|33.7463|72.8397
Murree|tehsil|Rawalpindi|Rawalpindi|33.9070|73.3943
Kallar Syedan|tehsil|Rawalpindi|Rawalpindi|33.4650|73.3830
Hazro|tehsil|Rawalpindi|Attock|33.9100|72.4920
Hassan Abdal|tehsil|Rawalpindi|Attock|33.8195|72.6890
Fateh Jang|tehsil|Rawalpindi|Attock|33.5670|72.6410
Pindi Gheb|tehsil|Rawalpindi|Attock|33.2400|72.2660
Jand|tehsil|Rawalpindi|Attock|33.4330|72.0170
Choa Saidan Shah|tehsil|Rawalpindi|Chakwal|32.7200|72.9840
Lawa|tehsil|Rawalpindi|Talagang|32.6950|72.0500
Dina|tehsil|Rawalpindi|Jhelum|33.0280|73.6010
Sohawa|tehsil|Rawalpindi|Jhelum|33.1300|73.4260
Pind Dadan Khan|tehsil|Rawalpindi|Jhelum|32.5860|73.0450
Bhalwal|tehsil|Sargodha|Sargodha|32.2650|72.8990
Bhera|town|Sargodha|Sargodha|32.4820|72.9080
Kot Momin|tehsil|Sargodha|Sargodha|32.1880|73.0290
Sillanwali|tehsil|Sargodha|Sargodha|31.8250|72.5400
Shahpur|tehsil|Sargodha|Sargodha|32.2680|72.4730
Quaidabad|tehsil|Sargodha|Khushab|32.3330|72.0170
Noorpur Thal|tehsil|Sargodha|Khushab|31.8710|71.9050
Naushera|tehsil|Sargodha|Khushab|32.5680|72.1460
Isa Khel|tehsil|Sargodha|Mianwali|32.6730|71.2720
Piplan|tehsil|Sargodha|Mianwali|32.2870|71.3660
Kalur Kot|tehsil|Sargodha|Bhakkar|32.1560|71.2670
Darya Khan|tehsil|Sargodha|Bhakkar|31.7890|71.1020
Mankera|tehsil|Sargodha|Bhakkar|31.3870|71.4400
Shujabad|tehsil|Multan|Multan|29.7700|71.2950
Jalalpur Pirwala|tehsil|Multan|Multan|29.5050|71.2220
Kabirwala|tehsil|Multan|Khanewal|30.4050|71.8660
Mian Channu|tehsil|Multan|Khanewal|30.4400|72.3560
Jahanian|tehsil|Multan|Khanewal|30.3060|71.8170
Dunyapur|tehsil|Multan|Lodhran|29.8030|71.7430
Kahror Pakka|tehsil|Multan|Lodhran|29.6240|71.9160
Burewala|tehsil|Multan|Vehari|30.1660|72.6530
Mailsi|tehsil|Multan|Vehari|29.8010|72.1760
Basti Malook|town|Multan|Multan|29.8590|71.5280
Qadirpur Ran|town|Multan|Multan|30.2910|71.6710
Ahmadpur East|tehsil|Bahawalpur|Bahawalpur|29.1453|71.2597
Hasilpur|tehsil|Bahawalpur|Bahawalpur|29.6920|72.5540
Khairpur Tamewali|tehsil|Bahawalpur|Bahawalpur|29.5810|72.2320
Yazman|tehsil|Bahawalpur|Bahawalpur|29.1210|71.7440
Chishtian|tehsil|Bahawalpur|Bahawalnagar|29.7970|72.8580
Haroonabad|tehsil|Bahawalpur|Bahawalnagar|29.6100|73.1380
Fort Abbas|tehsil|Bahawalpur|Bahawalnagar|29.1930|72.8550
Minchinabad|tehsil|Bahawalpur|Bahawalnagar|30.1650|73.5680
Khanpur|tehsil|Bahawalpur|Rahim Yar Khan|28.6470|70.6560
Sadiqabad|tehsil|Bahawalpur|Rahim Yar Khan|28.3060|70.1300
Liaqatpur|tehsil|Bahawalpur|Rahim Yar Khan|28.9360|70.9500
Model Town Bahawalpur|town|Bahawalpur|Bahawalpur|29.3905|71.6720
Cantt Bahawalpur|town|Bahawalpur|Bahawalpur|29.3780|71.7120
Kot Addu|tehsil|Dera Ghazi Khan|Muzaffargarh|30.4690|70.9660
Alipur|tehsil|Dera Ghazi Khan|Muzaffargarh|29.3820|70.9110
Jatoi|tehsil|Dera Ghazi Khan|Muzaffargarh|29.5180|70.8450
Chowk Azam|town|Dera Ghazi Khan|Layyah|30.9700|71.2200
Karor Lal Esan|tehsil|Dera Ghazi Khan|Layyah|31.2250|70.9520
Rojhan|tehsil|Dera Ghazi Khan|Rajanpur|28.6870|69.9530
Fazilpur|town|Dera Ghazi Khan|Rajanpur|29.3500|70.4300
Kot Chutta|tehsil|Dera Ghazi Khan|Dera Ghazi Khan|29.8830|70.6430
Chichawatni|tehsil|Sahiwal|Sahiwal|30.5300|72.7000
Depalpur|tehsil|Sahiwal|Okara|30.6700|73.6530
Renala Khurd|tehsil|Sahiwal|Okara|30.8780|73.5950
Arifwala|tehsil|Sahiwal|Pakpattan|30.2900|73.0660
Islamabad|city|Islamabad|Islamabad|33.6844|73.0479
Karachi|division|Karachi|Karachi|24.8607|67.0011|Sindh
Hyderabad|division|Hyderabad|Hyderabad|25.3960|68.3578|Sindh
Sukkur|division|Sukkur|Sukkur|27.7052|68.8574|Sindh
Larkana|division|Larkana|Larkana|27.5590|68.2120|Sindh
Mirpur Khas|division|Mirpur Khas|Mirpur Khas|25.5276|69.0126|Sindh
Shaheed Benazirabad|division|Shaheed Benazirabad|Shaheed Benazirabad|26.2442|68.4100|Sindh
Peshawar|division|Peshawar|Peshawar|34.0151|71.5249|Khyber Pakhtunkhwa
Mardan|division|Mardan|Mardan|34.1986|72.0404|Khyber Pakhtunkhwa
Malakand|division|Malakand|Malakand|34.5650|71.9300|Khyber Pakhtunkhwa
Hazara|division|Hazara|Abbottabad|34.1688|73.2215|Khyber Pakhtunkhwa
Kohat|division|Kohat|Kohat|33.5889|71.4429|Khyber Pakhtunkhwa
Bannu|division|Bannu|Bannu|32.9860|70.6049|Khyber Pakhtunkhwa
Dera Ismail Khan|division|Dera Ismail Khan|Dera Ismail Khan|31.8315|70.9017|Khyber Pakhtunkhwa
Quetta|division|Quetta|Quetta|30.1798|66.9750|Balochistan
Kalat|division|Kalat|Kalat|29.0266|66.5930|Balochistan
Makran|division|Makran|Kech|26.0023|63.0500|Balochistan
Nasirabad|division|Nasirabad|Nasirabad|28.2600|68.2200|Balochistan
Sibi|division|Sibi|Sibi|29.5430|67.8770|Balochistan
Zhob|division|Zhob|Zhob|31.3417|69.4486|Balochistan
Rakhshan|division|Rakhshan|Chagai|28.8830|64.4000|Balochistan
Gilgit|division|Gilgit|Gilgit|35.9208|74.3080|Gilgit-Baltistan
Baltistan|division|Baltistan|Skardu|35.2976|75.6337|Gilgit-Baltistan
Muzaffarabad|division|Muzaffarabad|Muzaffarabad|34.3700|73.4710|Azad Kashmir
Mirpur|division|Mirpur|Mirpur|33.1480|73.7510|Azad Kashmir
Poonch|division|Poonch|Rawalakot|33.8580|73.7600|Azad Kashmir
Karachi|district|Karachi|Karachi|24.8607|67.0011|Sindh
Hyderabad|district|Hyderabad|Hyderabad|25.3960|68.3578|Sindh
Jamshoro|district|Hyderabad|Jamshoro|25.4361|68.2806|Sindh
Thatta|district|Hyderabad|Thatta|24.7475|67.9235|Sindh
Badin|district|Hyderabad|Badin|24.6558|68.8383|Sindh
Dadu|district|Hyderabad|Dadu|26.7329|67.7763|Sindh
Matiari|district|Hyderabad|Matiari|25.5970|68.4467|Sindh
Tando Allahyar|district|Hyderabad|Tando Allahyar|25.4606|68.7174|Sindh
Tando Muhammad Khan|district|Hyderabad|Tando Muhammad Khan|25.1230|68.5360|Sindh
Sujawal|district|Hyderabad|Sujawal|24.6070|68.0800|Sindh
Sukkur|district|Sukkur|Sukkur|27.7052|68.8574|Sindh
Khairpur|district|Sukkur|Khairpur|27.5295|68.7592|Sindh
Ghotki|district|Sukkur|Ghotki|28.0060|69.3160|Sindh
Larkana|district|Larkana|Larkana|27.5590|68.2120|Sindh
Shikarpur|district|Larkana|Shikarpur|27.9571|68.6380|Sindh
Jacobabad|district|Larkana|Jacobabad|28.2810|68.4376|Sindh
Kashmore|district|Larkana|Kashmore|28.4326|69.5836|Sindh
Qambar Shahdadkot|district|Larkana|Qambar Shahdadkot|27.5900|68.0000|Sindh
Shaheed Benazirabad|district|Shaheed Benazirabad|Shaheed Benazirabad|26.2483|68.4096|Sindh
Nawabshah|town|Shaheed Benazirabad|Shaheed Benazirabad|26.2483|68.4096|Sindh
Sanghar|district|Shaheed Benazirabad|Sanghar|26.0464|68.9481|Sindh
Naushahro Feroze|district|Shaheed Benazirabad|Naushahro Feroze|26.8401|68.1227|Sindh
Mirpur Khas|district|Mirpur Khas|Mirpur Khas|25.5276|69.0126|Sindh
Umerkot|district|Mirpur Khas|Umerkot|25.3614|69.7362|Sindh
Tharparkar|district|Mirpur Khas|Tharparkar|24.7400|69.8000|Sindh
Mithi|town|Mirpur Khas|Tharparkar|24.7400|69.8000|Sindh
Clifton|town|Karachi|Karachi|24.8138|67.0299|Sindh
DHA Karachi|town|Karachi|Karachi|24.8048|67.0590|Sindh
Gulshan|town|Karachi|Karachi|24.9260|67.0920|Sindh
Saddar Karachi|town|Karachi|Karachi|24.8590|67.0280|Sindh
Korangi|town|Karachi|Karachi|24.8330|67.1400|Sindh
North Nazimabad|town|Karachi|Karachi|24.9340|67.0460|Sindh
Lyari|town|Karachi|Karachi|24.8700|66.9950|Sindh
Malir|town|Karachi|Karachi|24.8930|67.1960|Sindh
Landhi|town|Karachi|Karachi|24.8500|67.2000|Sindh
Latifabad|town|Hyderabad|Hyderabad|25.3670|68.3700|Sindh
Qasimabad|town|Hyderabad|Hyderabad|25.4150|68.3500|Sindh
Peshawar|district|Peshawar|Peshawar|34.0151|71.5249|Khyber Pakhtunkhwa
Charsadda|district|Peshawar|Charsadda|34.1482|71.7406|Khyber Pakhtunkhwa
Nowshera|district|Peshawar|Nowshera|34.0153|71.9747|Khyber Pakhtunkhwa
Khyber|district|Peshawar|Khyber|34.1000|71.1500|Khyber Pakhtunkhwa
Landi Kotal|town|Peshawar|Khyber|34.1000|71.1500|Khyber Pakhtunkhwa
Mohmand|district|Peshawar|Mohmand|34.3500|71.4000|Khyber Pakhtunkhwa
Mardan|district|Mardan|Mardan|34.1986|72.0404|Khyber Pakhtunkhwa
Swabi|district|Mardan|Swabi|34.1202|72.4698|Khyber Pakhtunkhwa
Swat|district|Malakand|Swat|34.7795|72.3600|Khyber Pakhtunkhwa
Mingora|town|Malakand|Swat|34.7795|72.3600|Khyber Pakhtunkhwa
Lower Dir|district|Malakand|Lower Dir|34.8270|71.8410|Khyber Pakhtunkhwa
Timergara|town|Malakand|Lower Dir|34.8270|71.8410|Khyber Pakhtunkhwa
Upper Dir|district|Malakand|Upper Dir|35.2000|72.0500|Khyber Pakhtunkhwa
Chitral|district|Malakand|Chitral|35.8511|71.7864|Khyber Pakhtunkhwa
Buner|district|Malakand|Buner|34.3940|72.6150|Khyber Pakhtunkhwa
Shangla|district|Malakand|Shangla|34.8870|72.5980|Khyber Pakhtunkhwa
Malakand|district|Malakand|Malakand|34.5650|71.9300|Khyber Pakhtunkhwa
Abbottabad|district|Hazara|Abbottabad|34.1688|73.2215|Khyber Pakhtunkhwa
Mansehra|district|Hazara|Mansehra|34.3302|73.1968|Khyber Pakhtunkhwa
Haripur|district|Hazara|Haripur|33.9946|72.9106|Khyber Pakhtunkhwa
Battagram|district|Hazara|Battagram|34.6800|73.0200|Khyber Pakhtunkhwa
Torghar|district|Hazara|Torghar|34.6200|72.8500|Khyber Pakhtunkhwa
Kohat|district|Kohat|Kohat|33.5889|71.4429|Khyber Pakhtunkhwa
Hangu|district|Kohat|Hangu|33.5310|71.0595|Khyber Pakhtunkhwa
Karak|district|Kohat|Karak|33.1160|71.0910|Khyber Pakhtunkhwa
Kurram|district|Kohat|Kurram|33.8990|70.1000|Khyber Pakhtunkhwa
Parachinar|town|Kohat|Kurram|33.8990|70.1000|Khyber Pakhtunkhwa
Orakzai|district|Kohat|Orakzai|33.7500|70.9000|Khyber Pakhtunkhwa
Bannu|district|Bannu|Bannu|32.9860|70.6049|Khyber Pakhtunkhwa
Lakki Marwat|district|Bannu|Lakki Marwat|32.6070|70.9110|Khyber Pakhtunkhwa
North Waziristan|district|Bannu|North Waziristan|32.9800|70.0700|Khyber Pakhtunkhwa
Miramshah|town|Bannu|North Waziristan|32.9800|70.0700|Khyber Pakhtunkhwa
Dera Ismail Khan|district|Dera Ismail Khan|Dera Ismail Khan|31.8315|70.9017|Khyber Pakhtunkhwa
Tank|district|Dera Ismail Khan|Tank|32.2170|70.3830|Khyber Pakhtunkhwa
South Waziristan|district|Dera Ismail Khan|South Waziristan|32.3000|69.5700|Khyber Pakhtunkhwa
Wana|town|Dera Ismail Khan|South Waziristan|32.3000|69.5700|Khyber Pakhtunkhwa
Quetta|district|Quetta|Quetta|30.1798|66.9750|Balochistan
Pishin|district|Quetta|Pishin|30.5818|66.9961|Balochistan
Killa Abdullah|district|Quetta|Killa Abdullah|30.7300|66.6500|Balochistan
Chaman|town|Quetta|Killa Abdullah|30.9210|66.4597|Balochistan
Kalat|district|Kalat|Kalat|29.0266|66.5930|Balochistan
Khuzdar|district|Kalat|Khuzdar|27.8110|66.6100|Balochistan
Mastung|district|Kalat|Mastung|29.7990|66.8450|Balochistan
Awaran|district|Kalat|Awaran|26.4500|65.2330|Balochistan
Lasbela|district|Kalat|Lasbela|25.8070|66.6220|Balochistan
Hub|town|Kalat|Lasbela|25.0220|66.8800|Balochistan
Uthal|town|Kalat|Lasbela|25.8070|66.6220|Balochistan
Kech|district|Makran|Kech|26.0023|63.0500|Balochistan
Turbat|town|Makran|Kech|26.0023|63.0500|Balochistan
Gwadar|district|Makran|Gwadar|25.1264|62.3225|Balochistan
Panjgur|district|Makran|Panjgur|26.9710|64.1000|Balochistan
Nasirabad|district|Nasirabad|Nasirabad|28.2600|68.2200|Balochistan
Jafarabad|district|Nasirabad|Jafarabad|28.3670|68.3330|Balochistan
Dera Allah Yar|town|Nasirabad|Jafarabad|28.3670|68.3330|Balochistan
Jhal Magsi|district|Nasirabad|Jhal Magsi|28.2830|67.4500|Balochistan
Kachhi|district|Nasirabad|Kachhi|29.0500|67.6500|Balochistan
Sohbatpur|district|Nasirabad|Sohbatpur|28.5170|68.5500|Balochistan
Sibi|district|Sibi|Sibi|29.5430|67.8770|Balochistan
Ziarat|district|Sibi|Ziarat|30.3810|67.7250|Balochistan
Harnai|district|Sibi|Harnai|30.1000|67.9300|Balochistan
Kohlu|district|Sibi|Kohlu|29.8960|69.2520|Balochistan
Dera Bugti|district|Sibi|Dera Bugti|29.0330|69.1500|Balochistan
Zhob|district|Zhob|Zhob|31.3417|69.4486|Balochistan
Loralai|district|Zhob|Loralai|30.3705|68.5979|Balochistan
Barkhan|district|Zhob|Barkhan|29.8970|69.5250|Balochistan
Musakhel|district|Zhob|Musakhel|30.8500|69.9000|Balochistan
Killa Saifullah|district|Zhob|Killa Saifullah|30.7000|68.3600|Balochistan
Chagai|district|Rakhshan|Chagai|28.8830|64.4000|Balochistan
Dalbandin|town|Rakhshan|Chagai|28.8830|64.4000|Balochistan
Nushki|district|Rakhshan|Nushki|29.5520|66.0220|Balochistan
Kharan|district|Rakhshan|Kharan|28.5830|65.4160|Balochistan
Washuk|district|Rakhshan|Washuk|27.3500|64.8000|Balochistan
Gilgit|district|Gilgit|Gilgit|35.9208|74.3080|Gilgit-Baltistan
Hunza|district|Gilgit|Hunza|36.3167|74.6500|Gilgit-Baltistan
Karimabad|town|Gilgit|Hunza|36.3167|74.6500|Gilgit-Baltistan
Ghizer|district|Gilgit|Ghizer|36.1730|73.7670|Gilgit-Baltistan
Gahkuch|town|Gilgit|Ghizer|36.1730|73.7670|Gilgit-Baltistan
Diamer|district|Gilgit|Diamer|35.4200|74.1000|Gilgit-Baltistan
Chilas|town|Gilgit|Diamer|35.4200|74.1000|Gilgit-Baltistan
Nagar|district|Gilgit|Nagar|36.2500|74.5000|Gilgit-Baltistan
Skardu|district|Baltistan|Skardu|35.2976|75.6337|Gilgit-Baltistan
Ghanche|district|Baltistan|Ghanche|35.1500|76.3330|Gilgit-Baltistan
Khaplu|town|Baltistan|Ghanche|35.1500|76.3330|Gilgit-Baltistan
Astore|district|Baltistan|Astore|35.3660|74.8600|Gilgit-Baltistan
Shigar|district|Baltistan|Shigar|35.4230|75.7330|Gilgit-Baltistan
Kharmang|district|Baltistan|Kharmang|35.0000|76.1000|Gilgit-Baltistan
Muzaffarabad|district|Muzaffarabad|Muzaffarabad|34.3700|73.4710|Azad Kashmir
Neelum|district|Muzaffarabad|Neelum|34.5800|73.9000|Azad Kashmir
Athmuqam|town|Muzaffarabad|Neelum|34.5800|73.9000|Azad Kashmir
Hattian|district|Muzaffarabad|Hattian|34.1700|73.7400|Azad Kashmir
Mirpur|district|Mirpur|Mirpur|33.1480|73.7510|Azad Kashmir
Kotli|district|Mirpur|Kotli|33.5160|73.9010|Azad Kashmir
Bhimber|district|Mirpur|Bhimber|32.9740|74.0790|Azad Kashmir
Rawalakot|district|Poonch|Rawalakot|33.8580|73.7600|Azad Kashmir
Bagh|district|Poonch|Bagh|33.9810|73.7720|Azad Kashmir
Haveli|district|Poonch|Haveli|33.9000|74.1000|Azad Kashmir
Sudhnoti|district|Poonch|Sudhnoti|33.7200|73.6800|Azad Kashmir
Pallandri|town|Poonch|Sudhnoti|33.7200|73.6800|Azad Kashmir
Kotri|tehsil|Hyderabad|Jamshoro|25.3650|68.3080|Sindh
Sehwan|tehsil|Hyderabad|Jamshoro|26.4240|67.8610|Sindh
Manjhand|tehsil|Hyderabad|Jamshoro|25.9500|68.2300|Sindh
Hala|tehsil|Hyderabad|Matiari|25.8100|68.4210|Sindh
Saeedabad|tehsil|Hyderabad|Matiari|25.9500|68.3800|Sindh
Matli|tehsil|Hyderabad|Badin|25.0430|68.6550|Sindh
Talhar|tehsil|Hyderabad|Badin|24.8840|68.8160|Sindh
Tando Bago|tehsil|Hyderabad|Badin|24.7880|68.9660|Sindh
Golarchi|tehsil|Hyderabad|Badin|24.5900|68.6900|Sindh
Mehar|tehsil|Hyderabad|Dadu|27.1800|67.8230|Sindh
Khairpur Nathan Shah|tehsil|Hyderabad|Dadu|27.0920|67.7340|Sindh
Johi|tehsil|Hyderabad|Dadu|26.6920|67.6130|Sindh
Mirpur Sakro|tehsil|Hyderabad|Thatta|24.5470|67.6280|Sindh
Gharo|town|Hyderabad|Thatta|24.7410|67.5850|Sindh
Jati|tehsil|Hyderabad|Sujawal|24.3540|68.2670|Sindh
Mirpur Bathoro|tehsil|Hyderabad|Sujawal|24.7280|68.2600|Sindh
Chamber|tehsil|Hyderabad|Tando Allahyar|25.2930|68.8110|Sindh
Jhando Mari|tehsil|Hyderabad|Tando Allahyar|25.4800|68.6200|Sindh
Digri|tehsil|Mirpur Khas|Mirpur Khas|25.1570|69.1100|Sindh
Kot Ghulam Muhammad|tehsil|Mirpur Khas|Mirpur Khas|25.2900|69.2500|Sindh
Jhuddo|tehsil|Mirpur Khas|Mirpur Khas|24.9660|69.3000|Sindh
Kunri|tehsil|Mirpur Khas|Umerkot|25.1780|69.5650|Sindh
Samaro|tehsil|Mirpur Khas|Umerkot|25.2830|69.3960|Sindh
Pithoro|tehsil|Mirpur Khas|Umerkot|25.5120|69.3780|Sindh
Islamkot|tehsil|Mirpur Khas|Tharparkar|24.6920|70.1790|Sindh
Diplo|tehsil|Mirpur Khas|Tharparkar|24.4660|69.5810|Sindh
Chachro|tehsil|Mirpur Khas|Tharparkar|25.1100|70.2500|Sindh
Nagarparkar|tehsil|Mirpur Khas|Tharparkar|24.3560|70.7550|Sindh
Shahdadpur|tehsil|Shaheed Benazirabad|Sanghar|25.9240|68.6220|Sindh
Tando Adam|tehsil|Shaheed Benazirabad|Sanghar|25.7680|68.6610|Sindh
Khipro|tehsil|Shaheed Benazirabad|Sanghar|25.8280|69.3770|Sindh
Sinjhoro|tehsil|Shaheed Benazirabad|Sanghar|26.0300|68.8050|Sindh
Moro|tehsil|Shaheed Benazirabad|Naushahro Feroze|26.6630|68.0000|Sindh
Kandiaro|tehsil|Shaheed Benazirabad|Naushahro Feroze|27.0600|68.2100|Sindh
Bhiria|tehsil|Shaheed Benazirabad|Naushahro Feroze|27.2000|68.1900|Sindh
Mehrabpur|tehsil|Shaheed Benazirabad|Naushahro Feroze|27.1000|68.0000|Sindh
Sakrand|tehsil|Shaheed Benazirabad|Shaheed Benazirabad|26.1380|68.2740|Sindh
Daur|tehsil|Shaheed Benazirabad|Shaheed Benazirabad|26.4550|68.3180|Sindh
Qazi Ahmed|tehsil|Shaheed Benazirabad|Shaheed Benazirabad|26.3700|68.1900|Sindh
Rohri|tehsil|Sukkur|Sukkur|27.6920|68.8950|Sindh
Pano Aqil|tehsil|Sukkur|Sukkur|27.8580|69.1110|Sindh
Salehpat|tehsil|Sukkur|Sukkur|27.5200|68.9800|Sindh
Kot Diji|tehsil|Sukkur|Khairpur|27.3410|68.7070|Sindh
Gambat|tehsil|Sukkur|Khairpur|27.3510|68.5200|Sindh
Ranipur|town|Sukkur|Khairpur|27.2870|68.5060|Sindh
Pir Jo Goth|town|Sukkur|Khairpur|27.4500|68.6200|Sindh
Mirpur Mathelo|tehsil|Sukkur|Ghotki|28.0200|69.5500|Sindh
Daharki|tehsil|Sukkur|Ghotki|28.0500|69.6900|Sindh
Ubauro|tehsil|Sukkur|Ghotki|28.1640|69.7170|Sindh
Ratodero|tehsil|Larkana|Larkana|27.8030|68.2890|Sindh
Dokri|tehsil|Larkana|Larkana|27.3740|68.0970|Sindh
Bakrani|tehsil|Larkana|Larkana|27.4500|68.2500|Sindh
Garhi Yasin|tehsil|Larkana|Shikarpur|27.9000|68.5200|Sindh
Lakhi|tehsil|Larkana|Shikarpur|27.8500|68.7000|Sindh
Thul|tehsil|Larkana|Jacobabad|28.2400|68.7750|Sindh
Garhi Khairo|tehsil|Larkana|Jacobabad|28.0600|67.9800|Sindh
Kandhkot|tehsil|Larkana|Kashmore|28.2450|69.1790|Sindh
Tangwani|tehsil|Larkana|Kashmore|28.2800|69.0000|Sindh
Shahdadkot|tehsil|Larkana|Qambar Shahdadkot|27.8470|67.9060|Sindh
Warah|tehsil|Larkana|Qambar Shahdadkot|27.4480|67.7940|Sindh
Mirokhan|tehsil|Larkana|Qambar Shahdadkot|27.7600|68.0900|Sindh
Orangi|town|Karachi|Karachi|24.9500|66.9900|Sindh
Nazimabad|town|Karachi|Karachi|24.9100|67.0300|Sindh
Baldia|town|Karachi|Karachi|24.9300|66.9600|Sindh
Keamari|town|Karachi|Karachi|24.8200|66.9800|Sindh
Bin Qasim|town|Karachi|Karachi|24.7900|67.3400|Sindh
Gadap|town|Karachi|Karachi|25.0500|67.1500|Sindh
Tangi|tehsil|Peshawar|Charsadda|34.3000|71.6500|Khyber Pakhtunkhwa
Shabqadar|tehsil|Peshawar|Charsadda|34.2200|71.5600|Khyber Pakhtunkhwa
Pabbi|tehsil|Peshawar|Nowshera|34.0100|71.8000|Khyber Pakhtunkhwa
Jehangira|tehsil|Peshawar|Nowshera|33.9700|72.2200|Khyber Pakhtunkhwa
Takht Bhai|tehsil|Mardan|Mardan|34.3170|71.9170|Khyber Pakhtunkhwa
Katlang|tehsil|Mardan|Mardan|34.3700|72.0800|Khyber Pakhtunkhwa
Topi|tehsil|Mardan|Swabi|34.0700|72.6200|Khyber Pakhtunkhwa
Kabal|tehsil|Malakand|Swat|34.7900|72.2800|Khyber Pakhtunkhwa
Matta|tehsil|Malakand|Swat|35.0900|72.4200|Khyber Pakhtunkhwa
Khwazakhela|tehsil|Malakand|Swat|34.9300|72.4700|Khyber Pakhtunkhwa
Bahrain|town|Malakand|Swat|35.2000|72.5500|Khyber Pakhtunkhwa
Kalam|town|Malakand|Swat|35.4800|72.5800|Khyber Pakhtunkhwa
Daggar|tehsil|Malakand|Buner|34.5100|72.4800|Khyber Pakhtunkhwa
Alpuri|town|Malakand|Shangla|34.9200|72.6300|Khyber Pakhtunkhwa
Batkhela|town|Malakand|Malakand|34.6170|71.9710|Khyber Pakhtunkhwa
Drosh|tehsil|Malakand|Chitral|35.5600|71.8000|Khyber Pakhtunkhwa
Mastuj|tehsil|Malakand|Chitral|36.2800|72.5200|Khyber Pakhtunkhwa
Havelian|tehsil|Hazara|Abbottabad|34.0530|73.1500|Khyber Pakhtunkhwa
Nawanshehr|tehsil|Hazara|Abbottabad|34.1600|73.2600|Khyber Pakhtunkhwa
Balakot|tehsil|Hazara|Mansehra|34.5500|73.3500|Khyber Pakhtunkhwa
Oghi|tehsil|Hazara|Mansehra|34.5000|73.0200|Khyber Pakhtunkhwa
Ghazi|tehsil|Hazara|Haripur|33.9800|72.6600|Khyber Pakhtunkhwa
Khanpur Haripur|tehsil|Hazara|Haripur|33.8200|72.9300|Khyber Pakhtunkhwa
Lachi|tehsil|Kohat|Kohat|33.3900|71.3400|Khyber Pakhtunkhwa
Thall|tehsil|Kohat|Hangu|33.3600|70.5500|Khyber Pakhtunkhwa
Domel|tehsil|Bannu|Bannu|32.9500|70.7400|Khyber Pakhtunkhwa
Kulachi|tehsil|Dera Ismail Khan|Dera Ismail Khan|31.9300|70.4600|Khyber Pakhtunkhwa
Paharpur|tehsil|Dera Ismail Khan|Dera Ismail Khan|32.1000|70.9700|Khyber Pakhtunkhwa
Paroa|tehsil|Dera Ismail Khan|Dera Ismail Khan|31.7500|70.7500|Khyber Pakhtunkhwa
Pasni|town|Makran|Gwadar|25.2630|63.4690|Balochistan
Jiwani|town|Makran|Gwadar|25.0500|61.7410|Balochistan
Ormara|town|Makran|Gwadar|25.2080|64.6360|Balochistan
Bela|tehsil|Kalat|Lasbela|26.2270|66.3110|Balochistan
Gadani|town|Kalat|Lasbela|25.1180|66.7320|Balochistan
Wadh|tehsil|Kalat|Khuzdar|27.3400|66.3500|Balochistan
Duki|tehsil|Zhob|Loralai|30.1500|68.5700|Balochistan
Muslim Bagh|town|Zhob|Killa Saifullah|30.8200|67.7300|Balochistan
Sui|town|Sibi|Dera Bugti|28.6400|69.1800|Balochistan
Dera Murad Jamali|town|Nasirabad|Nasirabad|28.5460|68.2230|Balochistan
Usta Muhammad|tehsil|Nasirabad|Jafarabad|28.1800|68.0500|Balochistan
Nok Kundi|town|Rakhshan|Chagai|28.8200|62.7500|Balochistan
Taftan|town|Rakhshan|Chagai|28.9700|61.5300|Balochistan
Danyore|town|Gilgit|Gilgit|35.9200|74.3800|Gilgit-Baltistan
Juglot|town|Gilgit|Gilgit|35.7000|74.6200|Gilgit-Baltistan
Aliabad|town|Gilgit|Hunza|36.3100|74.6200|Gilgit-Baltistan
Gulmit|town|Gilgit|Hunza|36.3900|74.8600|Gilgit-Baltistan
Dadyal|tehsil|Mirpur|Mirpur|33.2200|73.7500|Azad Kashmir
Chakswari|tehsil|Mirpur|Mirpur|33.2600|73.8200|Azad Kashmir
Khuiratta|tehsil|Mirpur|Kotli|33.3600|74.0300|Azad Kashmir
Sehnsa|tehsil|Mirpur|Kotli|33.5200|73.7500|Azad Kashmir
Barnala|tehsil|Mirpur|Bhimber|32.9800|74.2000|Azad Kashmir
Samahni|tehsil|Mirpur|Bhimber|32.9000|74.2000|Azad Kashmir
Dhirkot|tehsil|Poonch|Bagh|34.0300|73.5800|Azad Kashmir
Garhi Dupatta|tehsil|Muzaffarabad|Muzaffarabad|34.2300|73.6100|Azad Kashmir
Hajira|town|Poonch|Rawalakot|33.7700|73.8900|Azad Kashmir
Islamabad|district|Islamabad|Islamabad|33.6844|73.0479|Islamabad
F-8|town|Islamabad|Islamabad|33.7130|73.0400|Islamabad
G-10|town|Islamabad|Islamabad|33.6820|73.0250|Islamabad
Blue Area|town|Islamabad|Islamabad|33.7100|73.0580|Islamabad
"""


def _load():
    places = []
    seen = set()
    for line in _RAW.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) == 6:
            name, kind, division, district, lat, lng = parts
            province = "Islamabad" if division == "Islamabad" or name == "Islamabad" else "Punjab"
        elif len(parts) == 7:
            name, kind, division, district, lat, lng, province = parts
        else:
            continue
        key = (name.lower(), kind)
        if key in seen:
            continue
        seen.add(key)
        places.append(
            {
                "name": name,
                "kind": kind,
                "division": division,
                "district": district,
                "province": province,
                "lat": float(lat),
                "lng": float(lng),
                "detail": f"{kind.title()} · {district}, {province}",
            }
        )
    return places


PLACES = _load()


PROVINCES = (
    "Punjab",
    "Sindh",
    "Khyber Pakhtunkhwa",
    "Balochistan",
    "Islamabad",
    "Gilgit-Baltistan",
    "Azad Kashmir",
)


def in_pakistan(lat: float, lng: float) -> bool:
    return 23.50 <= lat <= 37.30 and 60.70 <= lng <= 77.05


def in_punjab(lat: float, lng: float) -> bool:
    return in_pakistan(lat, lng)


def province_for_division(division: str) -> str:
    needle = (division or "").strip().lower()
    for place in PLACES:
        if place["kind"] == "division" and place["name"].lower() == needle:
            return place["province"]
    for place in PLACES:
        if place["division"].lower() == needle:
            return place["province"]
    return ""


def province_center(province: str):
    needle = (province or "").strip().lower()
    preferred = {
        "punjab": "lahore",
        "sindh": "karachi",
        "khyber pakhtunkhwa": "peshawar",
        "balochistan": "quetta",
        "islamabad": "islamabad",
        "gilgit-baltistan": "gilgit",
        "azad kashmir": "muzaffarabad",
    }.get(needle, "")
    for place in PLACES:
        if place["kind"] == "division" and place["province"].lower() == needle and place["name"].lower() == preferred:
            return place
    for place in PLACES:
        if place["kind"] == "division" and place["province"].lower() == needle:
            return place
    return None


def search_local(query: str, limit: int = 8):
    needle = query.strip().lower()
    if not needle:
        return [place for place in PLACES if place["kind"] == "division"]
    scored = []
    for place in PLACES:
        name = place["name"].lower()
        blob = f"{name} {place['district'].lower()} {place['division'].lower()} {place['province'].lower()}"
        if name == needle:
            score = 0
        elif name.startswith(needle):
            score = 1
        elif needle in blob:
            score = 2
        else:
            continue
        scored.append((score, 0 if place["kind"] == "district" else 1, place["name"], place))
    scored.sort(key=lambda item: item[:3])
    return [item[3] for item in scored[:limit]]


def find_place(name: str):
    needle = (name or "").strip().lower()
    for place in PLACES:
        if place["name"].lower() == needle and place["kind"] in ("district", "city", "tehsil", "town"):
            return place
    for place in PLACES:
        if place["name"].lower() == needle:
            return place
    return None


def nearest_place(lat: float, lng: float):
    best = None
    best_dist = 10**9
    for place in PLACES:
        if place["kind"] not in ("district", "tehsil", "town", "city"):
            continue
        dist = (place["lat"] - lat) ** 2 + (place["lng"] - lng) ** 2
        if dist < best_dist:
            best = place
            best_dist = dist
    return best


def search_streets(query: str):
    needle = query.strip()
    if len(needle) < 3:
        return []
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {
            "q": f"{needle}, Pakistan",
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 5,
            "countrycodes": "pk",
        }
    )
    request = urllib.request.Request(url, headers={"User-Agent": "PocketDoc/1.0 (clinic finder)"})
    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            payload = json.loads(response.read().decode())
    except Exception:
        return []
    hits = []
    for item in payload:
        lat = float(item["lat"])
        lng = float(item["lon"])
        if not in_pakistan(lat, lng):
            continue
        address = item.get("address") or {}
        district = address.get("state_district") or address.get("county") or address.get("city") or ""
        label = item.get("name") or (item.get("display_name") or "").split(",")[0]
        near = nearest_place(lat, lng)
        hits.append(
            {
                "name": label,
                "kind": "street" if address.get("road") or address.get("suburb") else (item.get("addresstype") or "place"),
                "division": near["division"] if near else "",
                "district": district or (near["district"] if near else ""),
                "province": near["province"] if near else "",
                "lat": lat,
                "lng": lng,
                "detail": item.get("display_name") or label,
            }
        )
    return hits
