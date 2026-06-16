#!/usr/bin/env python3
"""Generate the curated Thai A1 starter corpus."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "minicloze-lib" / "corpora"
GENERATED = CORPORA / "generated"
ID_START = -400000
SOURCE = "Codex-curated Thai A1 starter seed list"


RAW = """
สวัสดี|hello|greeting|สวัสดีครับครู::Hello, teacher.|แม่พูดสวัสดีตอนเช้า::Mother says hello in the morning.|เด็กพูดสวัสดีกับเพื่อน::The child says hello to a friend.
ขอบคุณ|thank you|polite phrase|ขอบคุณครับพ่อ::Thank you, Dad.|ฉันขอบคุณครู::I thank the teacher.|เธอขอบคุณเพื่อนที่ช่วย::She thanks her friend for helping.
ขอโทษ|sorry|polite phrase|ขอโทษครับฉันมาช้า::Sorry, I am late.|เด็กพูดขอโทษกับแม่::The child says sorry to mother.|ขอโทษค่ะนี่ของคุณไหม::Sorry, is this yours?
ใช่|yes|response|ใช่ฉันเป็นนักเรียน::Yes, I am a student.|นี่ใช่บ้านคุณไหม::Is this your house?|เขาบอกว่าใช่::He says yes.
ไม่|no not|negation|ฉันไม่กินปลา::I do not eat fish.|เขาไม่อยู่บ้าน::He is not at home.|วันนี้ไม่ร้อน::Today is not hot.
ฉัน|I|pronoun|ฉันกินข้าวเช้า::I eat breakfast.|ฉันอยู่ในห้อง::I am in the room.|ฉันชอบชาอุ่น::I like warm tea.
คุณ|you|pronoun|คุณดื่มน้ำไหม::Do you drink water?|บ้านคุณอยู่ใกล้ตลาด::Your house is near the market.|ครูถามคุณตอนเช้า::The teacher asks you in the morning.
เขา|he she|pronoun|เขาอ่านหนังสือ::He reads a book.|เขาเป็นหมอในเมือง::She is a doctor in the city.|วันนี้เขามาโรงเรียน::He comes to school today.
เรา|we|pronoun|เรากินข้าวด้วยกัน::We eat together.|วันนี้เราไปตลาด::Today we go to the market.|เราเรียนภาษาไทย::We study Thai.
พวกเขา|they|pronoun|พวกเขานั่งในสวน::They sit in the park.|พวกเขาซื้อผลไม้::They buy fruit.|พวกเขาเดินไปโรงเรียน::They walk to school.
นี่|this here|demonstrative|นี่คือบ้านของฉัน::This is my house.|นี่ใช่กระเป๋าคุณไหม::Is this your bag?|นี่คือปากกาใหม่::This is a new pen.
นั่น|that|demonstrative|นั่นคือโรงเรียนของเรา::That is our school.|นั่นใช่ครูคุณไหม::Is that your teacher?|นั่นคือรถของพ่อ::That is father's car.
ใคร|who|question word|ใครอยู่ในห้อง::Who is in the room?|ครูถามว่าใครมา::The teacher asks who came.|ผู้ชายคนนั้นคือใคร::Who is that man?
อะไร|what|question word|นี่คืออะไร::What is this?|คุณกินอะไรตอนเช้า::What do you eat in the morning?|เด็กถามว่าอะไรอยู่ในกระเป๋า::The child asks what is in the bag.
ที่ไหน|where|question word|ตลาดอยู่ที่ไหน::Where is the market?|คุณไปที่ไหนวันนี้::Where are you going today?|สถานีอยู่ที่ไหน::Where is the station?
เมื่อไหร่|when|question word|คุณมาถึงเมื่อไหร่::When do you arrive?|เราไปตลาดเมื่อไหร่::When do we go to the market?|ฝนจะหยุดเมื่อไหร่::When will the rain stop?
ทำไม|why|question word|ทำไมคุณมาช้า::Why are you late?|ทำไมเด็กไม่กินข้าว::Why does the child not eat rice?|ทำไมวันนี้ร้านปิด::Why is the shop closed today?
อย่างไร|how|question word|คุณเขียนชื่อนี้อย่างไร::How do you write this name?|เราจะไปตลาดอย่างไร::How will we go to the market?|ครูสอนอย่างไร::How does the teacher teach?
หนึ่ง|one|number|ฉันมีหนังสือหนึ่งเล่ม::I have one book.|มีเด็กหนึ่งคนในห้อง::There is one child in the room.|ขอน้ำหนึ่งแก้วครับ::One glass of water, please.
สอง|two|number|เขามีปากกาสองด้าม::He has two pens.|เราซื้อตั๋วสองใบ::We buy two tickets.|แม่มีไข่สองฟอง::Mother has two eggs.
สาม|three|number|เด็กสามคนเล่นในสวน::Three children play in the park.|ฉันซื้อกล้วยสามลูก::I buy three bananas.|บนโต๊ะมีแก้วสามใบ::There are three glasses on the table.
สี่|four|number|เรามีเก้าอี้สี่ตัว::We have four chairs.|รถเมล์มาสี่โมง::The bus comes at four o'clock.|เขาซื้อแอปเปิลสี่ลูก::He buys four apples.
ห้า|five|number|ครูมีนักเรียนห้าคน::The teacher has five students.|ฉันตื่นห้าโมงเช้า::I wake up at five in the morning.|แม่ซื้อไข่ห้าฟอง::Mother buys five eggs.
สิบ|ten|number|ตั๋วราคาสิบบาท::The ticket costs ten baht.|ในห้องมีโต๊ะสิบตัว::There are ten tables in the room.|รถเมล์มาทุกสิบนาที::The bus comes every ten minutes.
คน|person|noun classifier|คนนี้เป็นเพื่อนฉัน::This person is my friend.|ในร้านมีคนมาก::There are many people in the shop.|คนขับรถยิ้มให้เรา::The driver smiles at us.
ผู้ชาย|man|noun|ผู้ชายคนนั้นเป็นครู::That man is a teacher.|ผู้ชายอ่านหนังสือในสวน::The man reads a book in the park.|ผู้ชายซื้อกาแฟที่ร้าน::The man buys coffee at the shop.
ผู้หญิง|woman|noun|ผู้หญิงคนนั้นเป็นหมอ::That woman is a doctor.|ผู้หญิงขายผลไม้ในตลาด::The woman sells fruit in the market.|ผู้หญิงนั่งใกล้หน้าต่าง::The woman sits near the window.
เด็ก|child|noun|เด็กกินขนมปังกับนม::The child eats bread with milk.|เด็กเดินไปโรงเรียน::The child walks to school.|เด็กนอนในห้องเล็ก::The child sleeps in the small room.
พ่อ|father|family noun|พ่อขับรถไปทำงาน::Father drives to work.|พ่อซื้อปลาในตลาด::Father buys fish in the market.|พ่อนั่งอ่านหนังสือ::Father sits and reads a book.
แม่|mother|family noun|แม่ทำข้าวเย็น::Mother makes dinner.|แม่ดื่มชาร้อน::Mother drinks hot tea.|แม่ช่วยฉันเขียนชื่อ::Mother helps me write my name.
พี่|older sibling|family noun|พี่เรียนที่โรงเรียนใหญ่::My older sibling studies at a big school.|พี่ซื้อกระเป๋าใหม่::My older sibling buys a new bag.|พี่นั่งใกล้ฉัน::My older sibling sits near me.
น้อง|younger sibling|family noun|น้องกินกล้วยตอนเช้า::My younger sibling eats a banana in the morning.|น้องชอบเล่นในสวน::My younger sibling likes playing in the park.|น้องนอนเร็วคืนนี้::My younger sibling sleeps early tonight.
เพื่อน|friend|noun|เพื่อนมาที่บ้านฉัน::A friend comes to my house.|ฉันช่วยเพื่อนถือกระเป๋า::I help a friend carry a bag.|เพื่อนอ่านสมุดของเขา::The friend reads his notebook.
ครู|teacher|noun|ครูเขียนบนกระดาน::The teacher writes on the board.|ครูพูดช้าๆกับนักเรียน::The teacher speaks slowly to the students.|ครูนั่งที่โต๊ะหน้าห้อง::The teacher sits at the table at the front of the room.
นักเรียน|student|noun|นักเรียนอ่านหนังสือไทย::The student reads a Thai book.|นักเรียนถามครูอย่างสุภาพ::The student asks the teacher politely.|นักเรียนเดินเข้าโรงเรียน::The student walks into the school.
หมอ|doctor|noun|หมอทำงานที่โรงพยาบาล::The doctor works at the hospital.|หมอพูดกับแม่ของเด็ก::The doctor speaks with the child's mother.|วันนี้หมอไม่ว่าง::The doctor is not free today.
คนขับ|driver|noun|คนขับเปิดประตูรถ::The driver opens the car door.|คนขับรถเมล์พูดขอบคุณ::The bus driver says thank you.|คนขับรู้ทางไปสถานี::The driver knows the way to the station.
บ้าน|house home|noun|บ้านของฉันอยู่ใกล้สวน::My house is near the park.|พรุ่งนี้เราอยู่บ้าน::Tomorrow we stay home.|บ้านหลังนี้มีหน้าต่างใหญ่::This house has big windows.
ห้อง|room|noun|ห้องนี้เล็กแต่สะอาด::This room is small but clean.|เขานั่งในห้องเรียน::He sits in the classroom.|แม่เปิดประตูห้อง::Mother opens the room door.
โรงเรียน|school|noun|โรงเรียนอยู่ไกลจากบ้าน::The school is far from home.|เด็กไปโรงเรียนตอนเช้า::The child goes to school in the morning.|หน้าโรงเรียนมีต้นไม้::There are trees in front of the school.
ตลาด|market|noun|ตลาดเปิดตอนเช้า::The market opens in the morning.|ฉันซื้อผักที่ตลาด::I buy vegetables at the market.|ตลาดอยู่ใกล้สถานี::The market is near the station.
ร้าน|shop|noun|ร้านนี้ขายขนมปัง::This shop sells bread.|พ่อไปที่ร้านตอนเย็น::Father goes to the shop in the evening.|ร้านอยู่ริมถนน::The shop is by the road.
ร้านอาหาร|restaurant|noun|ร้านอาหารนี้มีข้าวอร่อย::This restaurant has tasty rice.|เราไปร้านอาหารกับเพื่อน::We go to a restaurant with friends.|ร้านอาหารปิดตอนกลางคืน::The restaurant closes at night.
โรงพยาบาล|hospital|noun|โรงพยาบาลอยู่ในเมือง::The hospital is in the city.|หมอเดินเข้าโรงพยาบาล::The doctor walks into the hospital.|แม่ไปโรงพยาบาลตอนเช้า::Mother goes to the hospital in the morning.
สถานี|station|noun|สถานีอยู่ใกล้ตลาด::The station is near the market.|รถเมล์หยุดที่สถานี::The bus stops at the station.|ฉันรอพ่อที่สถานี::I wait for father at the station.
เมือง|city town|noun|เมืองนี้ใหญ่และสวย::This city is big and beautiful.|เขาทำงานในเมือง::He works in the city.|เราเดินดูเมืองตอนเย็น::We walk around the city in the evening.
ถนน|road street|noun|ถนนนี้กว้างมาก::This road is very wide.|เด็กเดินข้างถนน::The child walks beside the road.|ร้านกาแฟอยู่ริมถนน::The coffee shop is by the road.
สวน|park garden|noun|สวนมีดอกไม้สวย::The park has beautiful flowers.|พวกเขานั่งในสวนตอนเย็น::They sit in the park in the evening.|ฉันเดินกับแม่ในสวน::I walk with mother in the park.
หนังสือ|book|noun|หนังสือเล่มนี้ใหม่::This book is new.|เด็กอ่านหนังสือบนเตียง::The child reads a book on the bed.|ครูให้หนังสือแก่นักเรียน::The teacher gives a book to a student.
สมุด|notebook|noun|สมุดของฉันอยู่ในกระเป๋า::My notebook is in the bag.|นักเรียนเปิดสมุดหน้าใหม่::The student opens a new page in the notebook.|แม่ซื้อสมุดให้ฉัน::Mother buys me a notebook.
ปากกา|pen|noun|ปากกาอยู่บนโต๊ะ::The pen is on the table.|ฉันเขียนด้วยปากกาสีดำ::I write with a black pen.|เขาซื้อปากกาใหม่สองด้าม::He buys two new pens.
โทรศัพท์|phone|noun|โทรศัพท์ของคุณดัง::Your phone is ringing.|ฉันดูเวลาในโทรศัพท์::I look at the time on the phone.|พ่อวางโทรศัพท์บนโต๊ะ::Father puts the phone on the table.
กระเป๋า|bag|noun|กระเป๋าใบนี้หนัก::This bag is heavy.|ฉันใส่สมุดในกระเป๋า::I put the notebook in the bag.|น้องถือกระเป๋าสีแดง::My younger sibling carries a red bag.
โต๊ะ|table desk|noun|โต๊ะอยู่ใกล้หน้าต่าง::The table is near the window.|บนโต๊ะมีข้าวและน้ำ::On the table there is rice and water.|ครูนั่งที่โต๊ะหน้าห้อง::The teacher sits at the table at the front of the room.
เก้าอี้|chair|noun|เก้าอี้ตัวนี้เล็ก::This chair is small.|เด็กนั่งบนเก้าอี้::The child sits on a chair.|ในห้องมีเก้าอี้หลายตัว::There are many chairs in the room.
ประตู|door|noun|ประตูบ้านเปิดอยู่::The house door is open.|กรุณาปิดประตูห้อง::Please close the room door.|คนขับเปิดประตูรถเมล์::The driver opens the bus door.
หน้าต่าง|window|noun|หน้าต่างห้องใหญ่::The room window is big.|แม่นั่งใกล้หน้าต่าง::Mother sits near the window.|ฉันเปิดหน้าต่างตอนเช้า::I open the window in the morning.
รถ|car vehicle|noun|รถของพ่ออยู่หน้าบ้าน::Father's car is in front of the house.|เขาขับรถไปตลาด::He drives to the market.|รถคันนี้เก่าแต่ดี::This car is old but good.
รถเมล์|bus|noun|รถเมล์มาช้าในวันนี้::The bus is late today.|ฉันขึ้นรถเมล์ไปโรงเรียน::I take the bus to school.|สถานีรถเมล์อยู่ใกล้ร้าน::The bus station is near the shop.
เงิน|money|noun|ฉันมีเงินเล็กน้อย::I have a little money.|แม่ให้เงินซื้อตั๋ว::Mother gives money to buy a ticket.|เขาวางเงินบนโต๊ะ::He puts the money on the table.
ตั๋ว|ticket|noun|ตั๋วรถเมล์อยู่ในกระเป๋า::The bus ticket is in the bag.|ฉันซื้อตั๋วสองใบ::I buy two tickets.|คุณมีตั๋วไหม::Do you have a ticket?
ข้าว|rice meal|noun|ข้าวร้อนอยู่บนโต๊ะ::Hot rice is on the table.|เรากินข้าวกับไก่::We eat rice with chicken.|แม่ทำข้าวเย็นให้ครอบครัว::Mother makes dinner for the family.
น้ำ|water|noun|ฉันดื่มน้ำเย็น::I drink cold water.|บนโต๊ะมีน้ำหนึ่งแก้ว::There is a glass of water on the table.|เด็กต้องการน้ำหลังวิ่ง::The child wants water after running.
ชา|tea|noun|แม่ดื่มชาตอนเช้า::Mother drinks tea in the morning.|ชาถ้วยนี้ไม่ร้อน::This cup of tea is not hot.|ฉันซื้อชาให้ครู::I buy tea for the teacher.
กาแฟ|coffee|noun|พ่อดื่มกาแฟทุกเช้า::Father drinks coffee every morning.|ร้านนี้ขายกาแฟดี::This shop sells good coffee.|เขาถือกาแฟหนึ่งแก้ว::He carries one cup of coffee.
นม|milk|noun|เด็กดื่มนมก่อนนอน::The child drinks milk before sleep.|นมอยู่ในตู้เย็น::The milk is in the refrigerator.|แม่ซื้อนมสองกล่อง::Mother buys two cartons of milk.
ขนมปัง|bread|noun|ขนมปังอยู่บนจาน::The bread is on the plate.|ฉันกินขนมปังกับนม::I eat bread with milk.|ร้านขายขนมปังใหม่::The shop sells fresh bread.
ไข่|egg|noun|แม่ทอดไข่ตอนเช้า::Mother fries eggs in the morning.|ในถุงมีไข่ห้าฟอง::There are five eggs in the bag.|เขากินไข่กับข้าว::He eats eggs with rice.
ผัก|vegetables|noun|ผักสดอยู่ในตลาด::Fresh vegetables are in the market.|ฉันซื้อผักให้แม่::I buy vegetables for mother.|เด็กกินผักกับข้าว::The child eats vegetables with rice.
ผลไม้|fruit|noun|ผลไม้อยู่บนโต๊ะ::The fruit is on the table.|พวกเขาซื้อผลไม้ที่ตลาด::They buy fruit at the market.|ฉันชอบผลไม้หวาน::I like sweet fruit.
กล้วย|banana|noun|กล้วยสีเหลืองอยู่ในจาน::The yellow banana is on the plate.|น้องกินกล้วยหนึ่งลูก::My younger sibling eats one banana.|แม่ซื้อกล้วยที่ตลาด::Mother buys bananas at the market.
แอปเปิล|apple|noun|แอปเปิลลูกนี้แดง::This apple is red.|ฉันแบ่งแอปเปิลให้เพื่อน::I share an apple with a friend.|ร้านมีแอปเปิลใหม่วันนี้::The shop has new apples today.
ปลา|fish|noun|พ่อซื้อปลาที่ตลาด::Father buys fish at the market.|ปลาอยู่ในจานข้าว::The fish is on the rice plate.|ฉันไม่กินปลาเย็น::I do not eat cold fish.
ไก่|chicken|noun|แม่ทำไก่กับข้าว::Mother cooks chicken with rice.|ร้านอาหารขายไก่อร่อย::The restaurant sells tasty chicken.|เขาซื้อไก่ให้ครอบครัว::He buys chicken for the family.
น้ำตาล|sugar|noun|ชาใส่น้ำตาลเล็กน้อย::The tea has a little sugar.|แม่ซื้อน้ำตาลที่ร้าน::Mother buys sugar at the shop.|ฉันไม่ใส่น้ำตาลในกาแฟ::I do not put sugar in coffee.
เกลือ|salt|noun|แม่ใส่เกลือในปลา::Mother puts salt on the fish.|เกลืออยู่ข้างน้ำตาล::The salt is beside the sugar.|อาหารนี้มีเกลือมาก::This food has a lot of salt.
วันนี้|today|time word|วันนี้แดดดี::Today the sunshine is good.|วันนี้ฉันไปโรงเรียน::Today I go to school.|วันนี้ร้านอาหารปิดเร็ว::Today the restaurant closes early.
พรุ่งนี้|tomorrow|time word|พรุ่งนี้เราไปตลาด::Tomorrow we go to the market.|พรุ่งนี้ครูไม่ว่าง::Tomorrow the teacher is not free.|พรุ่งนี้ฉันตื่นเช้า::Tomorrow I wake up early.
เมื่อวาน|yesterday|time word|เมื่อวานฝนตกหนัก::Yesterday it rained hard.|เมื่อวานฉันซื้อหนังสือ::Yesterday I bought a book.|เมื่อวานเขามาบ้านเรา::Yesterday he came to our house.
เช้า|morning|time word|เช้านี้อากาศเย็น::This morning the weather is cool.|ฉันดื่มกาแฟตอนเช้า::I drink coffee in the morning.|แม่ไปตลาดแต่เช้า::Mother goes to the market early.
เย็น|evening cool|time word adjective|ตอนเย็นเราเดินในสวน::In the evening we walk in the park.|น้ำแก้วนี้เย็นมาก::This glass of water is very cold.|แม่ทำข้าวเย็นให้เรา::Mother makes dinner for us.
คืน|night|time word|คืนนี้น้องนอนเร็ว::Tonight my younger sibling sleeps early.|คืนวันศุกร์ตลาดเปิดช้า::On Friday night the market stays open late.|ฉันอ่านหนังสือกลางคืน::I read a book at night.
วัน|day|time word|วันจันทร์ฉันไปโรงเรียน::On Monday I go to school.|วันนี้เป็นวันดี::Today is a good day.|เขาทำงานทุกวัน::He works every day.
เวลา|time|noun|เวลาเรียนเริ่มเช้า::Class time starts in the morning.|คุณมีเวลาไหม::Do you have time?|ฉันดูเวลาในโทรศัพท์::I check the time on the phone.
ฝน|rain|noun|ฝนตกตอนเย็น::It rains in the evening.|วันนี้ฝนไม่ตก::Today it does not rain.|เด็กวิ่งกลับบ้านตอนฝนมา::The child runs home when the rain comes.
แดด|sunshine|noun|แดดแรงบนถนน::The sunshine is strong on the road.|วันนี้มีแดดดี::Today has good sunshine.|เด็กนั่งใต้ต้นไม้เพราะแดดร้อน::The child sits under a tree because the sun is hot.
ร้อน|hot|adjective|วันนี้อากาศร้อน::Today the weather is hot.|ชาถ้วยนี้ร้อนมาก::This cup of tea is very hot.|ข้าวยังร้อนอยู่::The rice is still hot.
หนาว|cold|adjective|ตอนเช้าอากาศหนาว::The morning weather is cold.|ฉันใส่เสื้อเพราะหนาว::I wear a shirt because it is cold.|คืนนี้เด็กไม่หนาว::Tonight the child is not cold.
ดี|good|adjective|ครูคนนี้ดีมาก::This teacher is very good.|วันนี้เป็นวันดี::Today is a good day.|กาแฟร้านนี้ดี::This shop's coffee is good.
ใหม่|new|adjective|ฉันมีสมุดใหม่::I have a new notebook.|รถใหม่อยู่หน้าบ้าน::The new car is in front of the house.|ร้านนี้เปิดใหม่::This shop is newly opened.
เก่า|old|adjective|หนังสือเก่าอยู่บนโต๊ะ::The old book is on the table.|รถเก่าของพ่อยังดี::Father's old car is still good.|บ้านเก่าอยู่ใกล้แม่น้ำ::The old house is near the river.
ใหญ่|big|adjective|โรงเรียนนี้ใหญ่::This school is big.|เขามีกระเป๋าใหญ่::He has a big bag.|หน้าต่างใหญ่เปิดอยู่::The big window is open.
เล็ก|small|adjective|ห้องเล็กอยู่ข้างครัว::The small room is beside the kitchen.|เด็กถือแก้วเล็ก::The child holds a small glass.|ร้านเล็กขายชาและกาแฟ::The small shop sells tea and coffee.
สวย|beautiful|adjective|สวนนี้สวยมาก::This park is very beautiful.|ผู้หญิงใส่เสื้อสวย::The woman wears a beautiful shirt.|เมืองตอนกลางคืนสวย::The city is beautiful at night.
ง่าย|easy|adjective|บทเรียนนี้ง่าย::This lesson is easy.|คำถามง่ายสำหรับนักเรียน::The question is easy for the student.|ทางไปตลาดง่ายมาก::The way to the market is very easy.
ยาก|difficult|adjective|งานนี้ยากสำหรับฉัน::This work is difficult for me.|ข้อสอบไม่ยากวันนี้::The test is not difficult today.|ภาษาไทยยากแต่สนุก::Thai is difficult but fun.
แพง|expensive|adjective|กาแฟร้านนี้แพง::The coffee at this shop is expensive.|ตั๋วรถไฟแพงวันนี้::The train ticket is expensive today.|กระเป๋าใหม่แพงมาก::The new bag is very expensive.
ถูก|cheap correct|adjective|ขนมปังร้านนี้ถูก::The bread at this shop is cheap.|คำตอบของคุณถูก::Your answer is correct.|ตั๋วรถเมล์ถูกกว่าแท็กซี่::A bus ticket is cheaper than a taxi.
เร็ว|fast early|adjective adverb|รถเมล์วันนี้เร็ว::The bus is fast today.|เขาวิ่งเร็วในสวน::He runs fast in the park.|พรุ่งนี้ฉันตื่นเร็ว::Tomorrow I wake up early.
ช้า|slow late|adjective adverb|รถเมล์มาช้า::The bus comes late.|ครูพูดช้าให้เราเข้าใจ::The teacher speaks slowly so we understand.|เขาเดินช้าเพราะเหนื่อย::He walks slowly because he is tired.
ใกล้|near|adjective preposition|บ้านฉันอยู่ใกล้โรงเรียน::My house is near the school.|ร้านกาแฟใกล้สถานี::The coffee shop is near the station.|นั่งใกล้หน้าต่างดีไหม::Is sitting near the window good?
ไกล|far|adjective|โรงพยาบาลอยู่ไกลจากบ้าน::The hospital is far from home.|เขาเดินไกลทุกวัน::He walks far every day.|ตลาดไม่ไกลจากสถานี::The market is not far from the station.
ว่าง|free available|adjective|วันนี้ครูว่างตอนเย็น::The teacher is free this evening.|คุณว่างพรุ่งนี้ไหม::Are you free tomorrow?|เก้าอี้ตัวนี้ว่าง::This chair is free.
ไป|go|verb|ฉันไปโรงเรียนตอนเช้า::I go to school in the morning.|เราไปตลาดด้วยกัน::We go to the market together.|พ่อไปทำงานในเมือง::Father goes to work in the city.
มา|come|verb|แม่มาที่บ้านตอนเย็น::Mother comes home in the evening.|รถเมล์มาช้า::The bus comes late.|เพื่อนมาหาฉันพรุ่งนี้::A friend comes to see me tomorrow.
กิน|eat|verb|เด็กกินข้าวกับไข่::The child eats rice with egg.|ฉันกินผลไม้ตอนเช้า::I eat fruit in the morning.|เขาไม่กินผัก::He does not eat vegetables.
ดื่ม|drink|verb|ฉันดื่มน้ำเย็น::I drink cold water.|พ่อดื่มกาแฟตอนเช้า::Father drinks coffee in the morning.|เด็กดื่มนมก่อนนอน::The child drinks milk before bed.
อ่าน|read|verb|ฉันอ่านหนังสือใหม่::I read a new book.|ครูอ่านสมุดนักเรียน::The teacher reads the student's notebook.|เขาอ่านเมนูในร้านอาหาร::He reads the menu in the restaurant.
เขียน|write|verb|นักเรียนเขียนในสมุด::The student writes in a notebook.|ฉันเขียนชื่อบนตั๋ว::I write my name on the ticket.|ครูเขียนตัวเลขบนกระดาน::The teacher writes numbers on the board.
ดู|look watch|verb|เด็กดูโทรศัพท์ของแม่::The child looks at mother's phone.|เราไปดูเมืองตอนเย็น::We go to see the city in the evening.|ฉันดูเวลาแล้วไปโรงเรียน::I check the time and go to school.
ฟัง|listen|verb|นักเรียนฟังครูพูด::The students listen to the teacher speak.|ฉันฟังเพลงตอนกลางคืน::I listen to music at night.|แม่ฟังข่าวในรถ::Mother listens to the news in the car.
พูด|speak say|verb|ครูพูดภาษาไทยช้าๆ::The teacher speaks Thai slowly.|เด็กพูดกับเพื่อนในสวน::The child speaks with a friend in the park.|เขาพูดขอบคุณกับคนขับ::He says thank you to the driver.
เรียน|study learn|verb|เราเรียนภาษาไทยทุกวัน::We study Thai every day.|นักเรียนเรียนในห้องใหญ่::The students study in the big room.|ฉันชอบเรียนตอนเช้า::I like studying in the morning.
ทำ|do make|verb|แม่ทำอาหารเย็น::Mother makes dinner.|ฉันทำงานที่บ้าน::I work at home.|เด็กทำการบ้านบนโต๊ะ::The child does homework at the table.
ซื้อ|buy|verb|พ่อซื้อปลาในตลาด::Father buys fish at the market.|ฉันซื้อปากกาใหม่::I buy a new pen.|พวกเขาซื้อตั๋วรถเมล์::They buy bus tickets.
ขาย|sell|verb|ร้านนี้ขายชาและกาแฟ::This shop sells tea and coffee.|ผู้หญิงขายผักในตลาด::The woman sells vegetables at the market.|พ่อขายรถเก่า::Father sells the old car.
ชอบ|like|verb|ฉันชอบผลไม้หวาน::I like sweet fruit.|น้องชอบวิ่งในสวน::My younger sibling likes running in the park.|เขาชอบหนังสือเล่มนี้::He likes this book.
ต้องการ|want need|verb|เด็กต้องการน้ำเย็น::The child wants cold water.|ฉันต้องการตั๋วหนึ่งใบ::I need one ticket.|แม่ต้องการผักสด::Mother wants fresh vegetables.
มี|have there is|verb|ฉันมีสมุดและปากกา::I have a notebook and a pen.|ในห้องมีโต๊ะใหญ่::There is a big table in the room.|วันนี้มีแดดดี::Today there is good sunshine.
อยู่|be stay|verb|ฉันอยู่บ้านตอนเย็น::I am at home in the evening.|ตลาดอยู่ใกล้สถานี::The market is near the station.|เขาอยู่ในห้องกับครู::He is in the room with the teacher.
นอน|sleep lie down|verb|เด็กนอนบนเตียงเล็ก::The child sleeps on a small bed.|ฉันนอนเร็วคืนนี้::I sleep early tonight.|แมวนอนใต้โต๊ะ::The cat sleeps under the table.
นั่ง|sit|verb|ครูนั่งใกล้หน้าต่าง::The teacher sits near the window.|เรานั่งรถเมล์ไปเมือง::We take a bus to the city.|เด็กนั่งบนเก้าอี้สีแดง::The child sits on a red chair.
เดิน|walk|verb|ฉันเดินไปโรงเรียน::I walk to school.|พวกเขาเดินในสวนตอนเย็น::They walk in the park in the evening.|แม่เดินไปตลาดใกล้บ้าน::Mother walks to the market near home.
วิ่ง|run|verb|เด็กวิ่งในสนาม::The child runs in the field.|เขาวิ่งเร็วมาก::He runs very fast.|น้องวิ่งกลับบ้านตอนฝนตก::My younger sibling runs home when it rains.
ช่วย|help|verb|ฉันช่วยแม่ทำข้าวเย็น::I help mother make dinner.|เพื่อนช่วยถือกระเป๋า::A friend helps carry the bag.|ครูช่วยนักเรียนอ่านหนังสือ::The teacher helps the student read a book.
""".strip()


def parse_entries() -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for line_number, line in enumerate(RAW.splitlines(), 1):
        parts = line.split("|")
        if len(parts) != 6:
            raise ValueError(f"line {line_number}: expected 6 pipe-delimited fields")
        word, gloss, note, *sentence_pairs = [part.strip() for part in parts]
        sentences = []
        for pair in sentence_pairs:
            if "::" not in pair:
                raise ValueError(f"line {line_number}: missing sentence delimiter")
            target, text = pair.split("::", 1)
            target = target.strip()
            text = text.strip()
            if word not in target:
                raise ValueError(
                    f"line {line_number}: target sentence lacks word {word!r}: {target!r}"
                )
            sentences.append({"target": target, "text": text})
        entries.append(
            {
                "word": word,
                "gloss": gloss,
                "note": note,
                "sentences": sentences,
            }
        )

    words = [entry["word"] for entry in entries]
    if len(entries) != 125:
        raise ValueError(f"expected 125 entries, got {len(entries)}")
    if len(set(words)) != len(words):
        raise ValueError("duplicate Thai words in seed list")

    return entries


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_vocab(entries: list[dict[str, object]]) -> list[dict[str, str]]:
    return [
        {
            "word": str(entry["word"]),
            "gloss": str(entry["gloss"]),
            "note": str(entry["note"]),
            "source": SOURCE,
        }
        for entry in entries
    ]


def build_batch(entries: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "vocab_index": index,
            "word": entry["word"],
            "sentences": entry["sentences"],
        }
        for index, entry in enumerate(entries, 1)
    ]


def build_explanations(entries: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    rows = []
    current_id = ID_START
    for entry in entries:
        for _sentence in entry["sentences"]:  # type: ignore[index]
            rows.append(
                {
                    "id": current_id,
                    "words": [
                        {
                            "word": entry["word"],
                            "gloss": entry["gloss"],
                            "note": entry["note"],
                        }
                    ],
                }
            )
            current_id -= 1
    return {"data": rows}


def main() -> None:
    entries = parse_entries()
    write_json(CORPORA / "thai_a1_vocab.json", build_vocab(entries))
    write_json(GENERATED / "thai_001_125.json", build_batch(entries))
    write_json(CORPORA / "thai_a1_explanations.json", build_explanations(entries))
    print(f"thai: wrote {len(entries)} words and {len(entries) * 3} explanations")


if __name__ == "__main__":
    main()
