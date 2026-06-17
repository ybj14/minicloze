#!/usr/bin/env python3
"""Generate the curated Thai A1 corpus."""

from __future__ import annotations

import json
from pathlib import Path

from explanation_utils import build_thai_lexicon, explain_thai_sentence


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "minicloze-lib" / "corpora"
GENERATED = CORPORA / "generated"
ID_START = -400000
SOURCE = "Codex-curated Thai A1 seed list"


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

EXTRA_RAW = """
ผม|I male|pronoun|ผมเป็นนักเรียนใหม่::I am a new student.|ผมดื่มกาแฟตอนเช้า::I drink coffee in the morning.|วันนี้ผมไปทำงานเร็ว::Today I go to work early.
เธอ|she you|pronoun|เธออ่านหนังสือในสวน::She reads a book in the park.|เธอชอบชาเย็น::She likes iced tea.|ครูถามเธอเบาๆ::The teacher asks her softly.
มัน|it|pronoun|มันอยู่ใต้โต๊ะ::It is under the table.|มันไม่ใช่ของฉัน::It is not mine.|เด็กบอกว่ามันเล็กมาก::The child says it is very small.
ของ|of belonging|possessive word|หนังสือของฉันอยู่ในกระเป๋า::My book is in the bag.|นี่คือรถของพ่อ::This is father's car.|ชื่อของคุณสวยมาก::Your name is very beautiful.
กับ|with|preposition|ฉันไปตลาดกับแม่::I go to the market with mother.|เด็กเล่นกับเพื่อนในสวน::The child plays with friends in the park.|ครูพูดกับนักเรียนช้าๆ::The teacher speaks slowly with the students.
และ|and|conjunction|ฉันซื้อชาและขนมปัง::I buy tea and bread.|พ่อและแม่อยู่บ้าน::Father and mother are at home.|โต๊ะและเก้าอี้อยู่ในห้อง::The table and chair are in the room.
หรือ|or|conjunction|คุณต้องการชาหรือกาแฟ::Do you want tea or coffee?|วันนี้เราไปตลาดหรือร้านอาหาร::Are we going to the market or the restaurant today?|เขาจะอ่านหรือเขียน::Will he read or write?
แต่|but|conjunction|ห้องนี้เล็กแต่สะอาด::This room is small but clean.|ฉันชอบกาแฟแต่ไม่ใส่น้ำตาล::I like coffee but do not add sugar.|ฝนตกแต่เราไปโรงเรียน::It rains but we go to school.
เพราะ|because|conjunction|ฉันอยู่บ้านเพราะฝนตก::I stay home because it rains.|เด็กดื่มน้ำเพราะร้อน::The child drinks water because it is hot.|เขาเดินช้าเพราะเหนื่อย::He walks slowly because he is tired.
ถ้า|if|conjunction|ถ้าฝนตกฉันอยู่บ้าน::If it rains, I stay home.|ถ้าคุณว่างเราไปตลาด::If you are free, we go to the market.|ถ้าเด็กหิวแม่ทำข้าว::If the child is hungry, mother makes rice.
ให้|give for|verb preposition|ครูให้หนังสือนักเรียน::The teacher gives the student a book.|แม่ทำข้าวให้ฉัน::Mother makes rice for me.|ฉันให้ตั๋วกับเพื่อน::I give the ticket to a friend.
จาก|from|preposition|ฉันมาจากบ้าน::I come from home.|ตลาดอยู่ไกลจากโรงเรียน::The market is far from the school.|จดหมายจากแม่อยู่บนโต๊ะ::The letter from mother is on the table.
ถึง|arrive to until|preposition verb|รถเมล์ถึงสถานีแล้ว::The bus has arrived at the station.|ฉันเดินถึงบ้านตอนเย็น::I walk home in the evening.|จากตลาดถึงโรงเรียนไม่ไกล::From the market to the school is not far.
ใน|in inside|preposition|ในห้องมีโต๊ะใหญ่::There is a big table in the room.|ในกระเป๋ามีสมุดสองเล่ม::There are two notebooks in the bag.|ในตลาดมีผลไม้สด::There is fresh fruit in the market.
บน|on|preposition|บนโต๊ะมีแก้วน้ำ::There is a glass of water on the table.|หนังสืออยู่บนเก้าอี้::The book is on the chair.|แมวนอนบนเตียง::The cat sleeps on the bed.
ใต้|under|preposition|ใต้โต๊ะมีรองเท้า::There are shoes under the table.|สุนัขนอนใต้ต้นไม้::The dog sleeps under the tree.|กระเป๋าอยู่ใต้เก้าอี้::The bag is under the chair.
ข้าง|beside side|preposition noun|ข้างบ้านมีสวนเล็ก::Beside the house there is a small garden.|ฉันนั่งข้างเพื่อน::I sit beside a friend.|ร้านอยู่ข้างธนาคาร::The shop is beside the bank.
หน้า|front face|noun preposition|หน้าบ้านมีรถคันหนึ่ง::There is a car in front of the house.|เขายืนหน้าห้องเรียน::He stands in front of the classroom.|แม่รอหน้าร้านอาหาร::Mother waits in front of the restaurant.
ระหว่าง|between during|preposition|โต๊ะอยู่ระหว่างเก้าอี้สองตัว::The table is between two chairs.|ฉันอ่านหนังสือระหว่างรอรถเมล์::I read a book while waiting for the bus.|ตลาดอยู่ระหว่างโรงเรียนกับสถานี::The market is between the school and the station.
ตรง|straight exact|adjective adverb|ตรงนี้มีที่ว่าง::There is space here.|เดินตรงไปถึงตลาด::Walk straight to the market.|คำตอบนี้ตรงกับคำถาม::This answer matches the question.
พร้อม|ready together|adjective adverb|ฉันพร้อมไปโรงเรียน::I am ready to go to school.|อาหารพร้อมแล้วบนโต๊ะ::The food is ready on the table.|เราเดินพร้อมครู::We walk together with the teacher.
ยัง|still yet|adverb|เขายังอยู่ในห้อง::He is still in the room.|วันนี้ร้านยังเปิด::The shop is still open today.|ฉันยังไม่กินข้าว::I have not eaten yet.
ได้|can get|auxiliary verb|ฉันได้หนังสือใหม่::I got a new book.|คุณอ่านภาษาไทยได้ไหม::Can you read Thai?|เด็กได้ตั๋วจากแม่::The child gets a ticket from mother.
จะ|will|future marker|ฉันจะไปตลาดพรุ่งนี้::I will go to the market tomorrow.|เขาจะซื้อขนมปัง::He will buy bread.|เราจะเรียนตอนเช้า::We will study in the morning.
กำลัง|currently|progressive marker|ฉันกำลังอ่านหนังสือ::I am reading a book.|แม่กำลังทำอาหาร::Mother is making food.|เด็กกำลังเล่นในสวน::The child is playing in the park.
อยาก|want to|verb|ฉันอยากดื่มน้ำ::I want to drink water.|เด็กอยากไปสวน::The child wants to go to the park.|คุณอยากกินอะไร::What do you want to eat?
ต้อง|must need to|auxiliary verb|ฉันต้องไปโรงเรียน::I must go to school.|วันนี้เราต้องซื้อข้าว::Today we need to buy rice.|เด็กต้องนอนเร็ว::The child must sleep early.
สามารถ|be able to|auxiliary verb|ฉันสามารถอ่านประโยคนี้::I can read this sentence.|เขาสามารถขับรถได้::He can drive a car.|นักเรียนสามารถตอบคำถาม::The student can answer the question.
ครับ|polite particle male|particle|สวัสดีครับครู::Hello, teacher.|ขอบคุณครับพ่อ::Thank you, Dad.|ผมไปก่อนครับ::I will go first.
ค่ะ|polite particle female|particle|สวัสดีค่ะคุณครู::Hello, teacher.|ขอบคุณค่ะแม่::Thank you, mother.|นี่ของคุณค่ะ::This is yours.
ศูนย์|zero|number|คะแนนของฉันไม่ใช่ศูนย์::My score is not zero.|เด็กเขียนเลขศูนย์ในสมุด::The child writes zero in the notebook.|เบอร์โทรศัพท์ลงท้ายด้วยศูนย์::The phone number ends with zero.
หก|six|number|ฉันมีไข่หกฟอง::I have six eggs.|รถเมล์มาหกโมงเช้า::The bus comes at six in the morning.|เด็กหกคนอยู่ในห้อง::Six children are in the room.
เจ็ด|seven|number|เขาซื้อมะม่วงเจ็ดลูก::He buys seven mangoes.|เราเริ่มเรียนเจ็ดโมง::We start class at seven o'clock.|มีเก้าอี้เจ็ดตัวในห้อง::There are seven chairs in the room.
แปด|eight|number|แม่ซื้อส้มแปดลูก::Mother buys eight oranges.|ฉันนอนตอนแปดโมง::I sleep at eight o'clock.|นักเรียนแปดคนอ่านหนังสือ::Eight students read books.
เก้า|nine|number|ร้านเปิดเก้าโมงเช้า::The shop opens at nine in the morning.|เขามีปากกาเก้าด้าม::He has nine pens.|บนโต๊ะมีแก้วเก้าใบ::There are nine glasses on the table.
ร้อย|hundred|number|เสื้อราคาหนึ่งร้อยบาท::The shirt costs one hundred baht.|ในโรงเรียนมีนักเรียนร้อยคน::There are one hundred students in the school.|พ่อมีเงินร้อยบาท::Father has one hundred baht.
บาท|baht|money unit|ขนมปังราคาสิบบาท::The bread costs ten baht.|ฉันมีเงินสิบบาทในกระเป๋า::I have ten baht in my bag.|ตั๋วรถเมล์ห้าบาท::The bus ticket is five baht.
นาที|minute|time unit|รอฉันสองนาที::Wait for me for two minutes.|รถเมล์มาช้าสิบนาที::The bus is ten minutes late.|ครูพูดห้านาที::The teacher speaks for five minutes.
ชั่วโมง|hour|time unit|เราเรียนหนึ่งชั่วโมง::We study for one hour.|พ่อทำงานแปดชั่วโมง::Father works for eight hours.|ฉันเดินครึ่งชั่วโมง::I walk for half an hour.
สัปดาห์|week|time unit|สัปดาห์นี้ฉันเรียนทุกวัน::This week I study every day.|พ่อกลับบ้านสัปดาห์หน้า::Father comes home next week.|เราซื้อของหนึ่งครั้งต่อสัปดาห์::We shop once a week.
เดือน|month|time unit|เดือนนี้ฝนตกมาก::This month it rains a lot.|ฉันไปหาหมอเดือนหน้า::I go to the doctor next month.|เด็กเรียนภาษาไทยสามเดือน::The child studies Thai for three months.
ปี|year|time unit|ปีนี้ฉันอยู่เมืองไทย::This year I live in Thailand.|น้องอายุห้าปี::My younger sibling is five years old.|เราไปทะเลทุกปี::We go to the sea every year.
วันจันทร์|Monday|weekday|วันจันทร์ฉันไปโรงเรียน::On Monday I go to school.|ร้านเปิดวันจันทร์ตอนเช้า::The shop opens Monday morning.|ครูสอนภาษาไทยวันจันทร์::The teacher teaches Thai on Monday.
วันอังคาร|Tuesday|weekday|วันอังคารเรามีเรียน::On Tuesday we have class.|แม่ไปตลาดวันอังคาร::Mother goes to the market on Tuesday.|วันอังคารฝนไม่ตก::It does not rain on Tuesday.
วันพุธ|Wednesday|weekday|วันพุธฉันอ่านหนังสือ::On Wednesday I read a book.|พ่อกลับบ้านวันพุธ::Father comes home on Wednesday.|วันพุธร้านอาหารปิด::The restaurant is closed on Wednesday.
วันพฤหัสบดี|Thursday|weekday|วันพฤหัสบดีเราทำงาน::On Thursday we work.|ครูว่างวันพฤหัสบดี::The teacher is free on Thursday.|ฉันซื้อผักวันพฤหัสบดี::I buy vegetables on Thursday.
วันศุกร์|Friday|weekday|วันศุกร์เราไปสวน::On Friday we go to the park.|ร้านเปิดช้าวันศุกร์::The shop opens late on Friday.|เด็กดีใจในวันศุกร์::The child is happy on Friday.
วันเสาร์|Saturday|weekday|วันเสาร์ฉันอยู่บ้าน::On Saturday I stay home.|เราไปทะเลวันเสาร์::We go to the sea on Saturday.|วันเสาร์ตลาดมีคนมาก::On Saturday the market has many people.
วันอาทิตย์|Sunday|weekday|วันอาทิตย์ครอบครัวกินข้าวด้วยกัน::On Sunday the family eats together.|ฉันตื่นช้าวันอาทิตย์::I wake up late on Sunday.|วันอาทิตย์อากาศดี::The weather is good on Sunday.
ตอนนี้|now|time phrase|ตอนนี้ฉันอยู่บ้าน::Now I am at home.|ตอนนี้ฝนไม่ตก::It is not raining now.|ครูว่างตอนนี้ไหม::Is the teacher free now?
ครัว|kitchen|noun|ครัวอยู่หลังบ้าน::The kitchen is behind the house.|แม่ทำอาหารในครัว::Mother makes food in the kitchen.|ในครัวมีโต๊ะเล็ก::There is a small table in the kitchen.
ห้องน้ำ|bathroom|noun|ห้องน้ำอยู่ข้างห้องนอน::The bathroom is beside the bedroom.|เด็กล้างมือในห้องน้ำ::The child washes hands in the bathroom.|โรงแรมมีห้องน้ำสะอาด::The hotel has a clean bathroom.
ห้องนอน|bedroom|noun|ห้องนอนของฉันเล็ก::My bedroom is small.|น้องนอนในห้องนอน::My younger sibling sleeps in the bedroom.|ห้องนอนมีหน้าต่างใหญ่::The bedroom has a big window.
เตียง|bed|noun|เตียงอยู่ใกล้หน้าต่าง::The bed is near the window.|เด็กนอนบนเตียงเล็ก::The child sleeps on a small bed.|แม่วางผ้าห่มบนเตียง::Mother puts a blanket on the bed.
ตู้|cabinet closet|noun|ตู้เสื้อผ้าอยู่ในห้องนอน::The closet is in the bedroom.|ฉันเปิดตู้หาเสื้อ::I open the closet to look for a shirt.|บนตู้มีนาฬิกา::There is a clock on the cabinet.
ตู้เย็น|refrigerator|noun|ตู้เย็นอยู่ในครัว::The refrigerator is in the kitchen.|นมอยู่ในตู้เย็น::The milk is in the refrigerator.|แม่เปิดตู้เย็นเอาผัก::Mother opens the refrigerator and takes vegetables.
จาน|plate|noun|จานข้าวอยู่บนโต๊ะ::The rice plate is on the table.|ฉันล้างจานหลังอาหาร::I wash the plate after the meal.|เด็กถือจานเล็ก::The child holds a small plate.
ช้อน|spoon|noun|ช้อนอยู่ข้างจาน::The spoon is beside the plate.|แม่ใช้ช้อนตักซุป::Mother uses a spoon to scoop soup.|เด็กวางช้อนบนโต๊ะ::The child puts the spoon on the table.
ส้อม|fork|noun|ส้อมอยู่ในครัว::The fork is in the kitchen.|ฉันกินผลไม้ด้วยส้อม::I eat fruit with a fork.|พ่อซื้อส้อมใหม่สองคัน::Father buys two new forks.
มีด|knife|noun|มีดอยู่บนโต๊ะครัว::The knife is on the kitchen table.|แม่ใช้มีดหั่นผัก::Mother uses a knife to cut vegetables.|กรุณาวางมีดให้ไกลจากเด็ก::Please put the knife far from the child.
แก้ว|glass cup|noun|แก้วน้ำอยู่บนโต๊ะ::The water glass is on the table.|ฉันล้างแก้วหลังดื่มชา::I wash the cup after drinking tea.|เด็กถือแก้วเล็กอย่างระวัง::The child carefully holds a small glass.
ถ้วย|cup bowl|noun|ถ้วยชาร้อนมาก::The tea cup is very hot.|แม่วางถ้วยบนจาน::Mother puts the cup on the plate.|ฉันซื้อถ้วยใหม่ให้บ้าน::I buy a new cup for the house.
หม้อ|pot|noun|หม้อซุปอยู่บนเตา::The soup pot is on the stove.|แม่ล้างหม้อในครัว::Mother washes the pot in the kitchen.|ในหม้อมีข้าวร้อน::There is hot rice in the pot.
ไฟ|light fire|noun|ไฟในห้องเปิดอยู่::The light in the room is on.|กรุณาปิดไฟก่อนนอน::Please turn off the light before sleeping.|บนถนนมีไฟแดง::There is a red light on the road.
น้ำแข็ง|ice|noun|น้ำแข็งอยู่ในแก้ว::Ice is in the glass.|ฉันใส่น้ำแข็งในชา::I put ice in the tea.|ร้านขายน้ำแข็งตอนเช้า::The shop sells ice in the morning.
เสื้อ|shirt|noun|เสื้อสีขาวอยู่บนเตียง::The white shirt is on the bed.|ฉันใส่เสื้อใหม่วันนี้::I wear a new shirt today.|แม่ซักเสื้อให้ลูก::Mother washes the shirt for the child.
กางเกง|pants|noun|กางเกงสีดำอยู่ในตู้::The black pants are in the closet.|เขาซื้อกางเกงใหม่::He buys new pants.|เด็กใส่กางเกงสั้น::The child wears short pants.
รองเท้า|shoes|noun|รองเท้าอยู่ใต้โต๊ะ::The shoes are under the table.|ฉันใส่รองเท้าไปโรงเรียน::I wear shoes to school.|แม่ซื้อรองเท้าให้ลูก::Mother buys shoes for the child.
ถุงเท้า|socks|noun|ถุงเท้าอยู่ในกระเป๋า::The socks are in the bag.|เด็กใส่ถุงเท้าสีขาว::The child wears white socks.|ฉันซักถุงเท้าตอนเย็น::I wash socks in the evening.
หมวก|hat|noun|หมวกของพ่ออยู่บนเก้าอี้::Father's hat is on the chair.|แดดร้อนฉันใส่หมวก::The sun is hot, so I wear a hat.|เด็กซื้อหมวกสีแดง::The child buys a red hat.
แว่นตา|glasses|noun|แว่นตาอยู่ข้างหนังสือ::The glasses are beside the book.|ครูใส่แว่นตาอ่านสมุด::The teacher wears glasses to read the notebook.|พ่อหาแว่นตาในห้อง::Father looks for his glasses in the room.
นาฬิกา|clock watch|noun|นาฬิกาอยู่บนผนัง::The clock is on the wall.|ฉันดูนาฬิกาก่อนออกบ้าน::I look at the watch before leaving home.|นาฬิกาของแม่ใหม่มาก::Mother's watch is very new.
กุญแจ|key|noun|กุญแจบ้านอยู่ในกระเป๋า::The house key is in the bag.|ฉันหากุญแจไม่เจอ::I cannot find the key.|พ่อให้กุญแจแก่ฉัน::Father gives me the key.
ร่ม|umbrella|noun|ร่มสีดำอยู่หน้าประตู::The black umbrella is by the door.|ฝนตกฉันถือร่ม::It rains, so I carry an umbrella.|แม่ซื้อร่มใหม่ที่ตลาด::Mother buys a new umbrella at the market.
กระดาษ|paper|noun|กระดาษอยู่บนโต๊ะครู::The paper is on the teacher's desk.|นักเรียนเขียนชื่อบนกระดาษ::The student writes a name on the paper.|ฉันพับกระดาษเล็กๆ::I fold a small piece of paper.
ดินสอ|pencil|noun|ดินสออยู่ในกล่อง::The pencil is in the box.|เด็กเขียนด้วยดินสอ::The child writes with a pencil.|ครูให้ดินสอกับนักเรียน::The teacher gives a pencil to the student.
ยางลบ|eraser|noun|ยางลบอยู่ข้างดินสอ::The eraser is beside the pencil.|ฉันใช้ยางลบลบคำตอบ::I use an eraser to erase the answer.|เด็กซื้อยางลบใหม่::The child buys a new eraser.
กระดาน|board|noun|กระดานอยู่หน้าห้องเรียน::The board is at the front of the classroom.|ครูเขียนคำถามบนกระดาน::The teacher writes a question on the board.|นักเรียนมองกระดาน::The student looks at the board.
จดหมาย|letter|noun|จดหมายจากแม่อยู่บนโต๊ะ::The letter from mother is on the table.|ฉันเขียนจดหมายถึงเพื่อน::I write a letter to a friend.|พ่ออ่านจดหมายตอนเย็น::Father reads the letter in the evening.
กล่อง|box|noun|กล่องนี้เบามาก::This box is very light.|ในกล่องมีขนม::There are snacks in the box.|เด็กเปิดกล่องของขวัญ::The child opens the gift box.
ขวด|bottle|noun|ขวดน้ำอยู่ในกระเป๋า::The water bottle is in the bag.|ฉันซื้อขวดใหม่ที่ร้าน::I buy a new bottle at the shop.|แม่ล้างขวดในครัว::Mother washes the bottle in the kitchen.
ถุง|bag sack|noun|ถุงผักอยู่บนโต๊ะ::The vegetable bag is on the table.|ฉันถือถุงจากตลาด::I carry a bag from the market.|ในถุงมีส้มหลายลูก::There are many oranges in the bag.
จักรยาน|bicycle|noun|จักรยานอยู่หน้าบ้าน::The bicycle is in front of the house.|เด็กขี่จักรยานไปสวน::The child rides a bicycle to the park.|พ่อซ่อมจักรยานตอนเย็น::Father repairs the bicycle in the evening.
รถไฟ|train|noun|รถไฟมาถึงสถานี::The train arrives at the station.|เรานั่งรถไฟไปเมือง::We take the train to the city.|ตั๋วรถไฟอยู่ในกระเป๋า::The train ticket is in the bag.
เรือ|boat|noun|เรืออยู่ใกล้แม่น้ำ::The boat is near the river.|เราไปตลาดด้วยเรือ::We go to the market by boat.|เด็กดูเรือจากสะพาน::The child watches the boat from the bridge.
เครื่องบิน|airplane|noun|เครื่องบินอยู่ที่สนามบิน::The airplane is at the airport.|เขาขึ้นเครื่องบินไปกรุงเทพ::He boards an airplane to Bangkok.|เด็กวาดรูปเครื่องบิน::The child draws an airplane.
แท็กซี่|taxi|noun|แท็กซี่จอดหน้าร้าน::The taxi stops in front of the shop.|ฉันนั่งแท็กซี่ไปโรงแรม::I take a taxi to the hotel.|คนขับแท็กซี่รู้ทาง::The taxi driver knows the way.
ทาง|way road|noun|ทางไปตลาดง่ายมาก::The way to the market is very easy.|เขาถามทางไปสถานี::He asks the way to the station.|ทางนี้ใกล้กว่า::This way is nearer.
แผนที่|map|noun|แผนที่อยู่ในโทรศัพท์::The map is on the phone.|ฉันดูแผนที่ก่อนเดินทาง::I look at the map before traveling.|ครูวาดแผนที่บนกระดาน::The teacher draws a map on the board.
สะพาน|bridge|noun|สะพานอยู่ข้ามแม่น้ำ::The bridge is over the river.|เราเดินบนสะพานตอนเย็น::We walk on the bridge in the evening.|เด็กมองเรือจากสะพาน::The child looks at boats from the bridge.
แม่น้ำ|river|noun|แม่น้ำอยู่หลังหมู่บ้าน::The river is behind the village.|เราเดินใกล้แม่น้ำ::We walk near the river.|น้ำในแม่น้ำเย็นมาก::The water in the river is very cool.
ทะเล|sea|noun|ทะเลอยู่ไกลจากเมือง::The sea is far from the city.|วันเสาร์เราไปทะเล::On Saturday we go to the sea.|เด็กเล่นที่ชายหาดใกล้ทะเล::The child plays on the beach near the sea.
ภูเขา|mountain|noun|ภูเขาสูงอยู่ไกลๆ::The high mountain is far away.|เราเห็นภูเขาจากบ้าน::We see the mountain from the house.|อากาศบนภูเขาหนาว::The weather on the mountain is cold.
ชายหาด|beach|noun|ชายหาดมีทรายขาว::The beach has white sand.|เด็กวิ่งบนชายหาด::The child runs on the beach.|เราไปชายหาดตอนเย็น::We go to the beach in the evening.
สนาม|field yard|noun|สนามหน้าโรงเรียนกว้าง::The field in front of the school is wide.|เด็กวิ่งในสนาม::The child runs in the field.|พ่อดูฟุตบอลที่สนาม::Father watches football at the field.
สนามบิน|airport|noun|สนามบินอยู่ไกลจากบ้าน::The airport is far from home.|แท็กซี่ไปสนามบินตอนเช้า::The taxi goes to the airport in the morning.|เครื่องบินจอดที่สนามบิน::The airplane stops at the airport.
โรงแรม|hotel|noun|โรงแรมนี้สะอาดมาก::This hotel is very clean.|เราอยู่โรงแรมสองคืน::We stay at the hotel for two nights.|โรงแรมอยู่ใกล้สถานี::The hotel is near the station.
ธนาคาร|bank|noun|ธนาคารเปิดเก้าโมง::The bank opens at nine.|พ่อไปธนาคารตอนเช้า::Father goes to the bank in the morning.|ร้านอยู่ข้างธนาคาร::The shop is beside the bank.
ที่ทำงาน|workplace|noun|ที่ทำงานของแม่อยู่ในเมือง::Mother's workplace is in the city.|พ่อไปที่ทำงานด้วยรถเมล์::Father goes to work by bus.|ที่ทำงานอยู่ไกลจากบ้าน::The workplace is far from home.
สำนักงาน|office|noun|สำนักงานเปิดตอนเช้า::The office opens in the morning.|เขาทำงานในสำนักงานเล็ก::He works in a small office.|สำนักงานอยู่ชั้นสอง::The office is on the second floor.
ห้องสมุด|library|noun|ห้องสมุดอยู่ในโรงเรียน::The library is in the school.|ฉันอ่านหนังสือที่ห้องสมุด::I read a book at the library.|ห้องสมุดเงียบมาก::The library is very quiet.
มหาวิทยาลัย|university|noun|มหาวิทยาลัยอยู่ในเมืองใหญ่::The university is in a big city.|พี่เรียนที่มหาวิทยาลัย::My older sibling studies at a university.|รถเมล์ไปมหาวิทยาลัย::The bus goes to the university.
วัด|temple|noun|วัดอยู่ใกล้แม่น้ำ::The temple is near the river.|ครอบครัวไปวัดวันอาทิตย์::The family goes to the temple on Sunday.|หน้าวัดมีต้นไม้ใหญ่::There is a big tree in front of the temple.
ป้าย|sign stop|noun|ป้ายรถเมล์อยู่ริมถนน::The bus stop is by the road.|ฉันอ่านป้ายหน้าร้าน::I read the sign in front of the shop.|เด็กยืนใต้ป้ายใหญ่::The child stands under the big sign.
ไฟแดง|red light|noun|รถหยุดที่ไฟแดง::The car stops at the red light.|ไฟแดงอยู่ตรงทางแยก::The red light is at the intersection.|คนขับรอไฟแดง::The driver waits at the red light.
ครอบครัว|family|noun|ครอบครัวของฉันอยู่บ้าน::My family is at home.|วันอาทิตย์ครอบครัวกินข้าวด้วยกัน::On Sunday the family eats together.|ครอบครัวนี้มีเด็กสองคน::This family has two children.
ลูก|child offspring|family noun|ลูกของแม่ยังเล็ก::Mother's child is still small.|พ่อพาลูกไปโรงเรียน::Father takes the child to school.|ลูกช่วยแม่ล้างจาน::The child helps mother wash dishes.
ปู่|paternal grandfather|family noun|ปู่อยู่บ้านกับย่า::Grandfather is at home with grandmother.|ฉันไปหาปู่วันเสาร์::I visit grandfather on Saturday.|ปู่อ่านหนังสือพิมพ์ตอนเช้า::Grandfather reads the newspaper in the morning.
ย่า|paternal grandmother|family noun|ย่าทำขนมให้เรา::Grandmother makes snacks for us.|บ้านย่าอยู่ใกล้ตลาด::Grandmother's house is near the market.|ย่านั่งในสวนตอนเย็น::Grandmother sits in the park in the evening.
ตา|maternal grandfather eye|family noun|ตาเล่าเรื่องเก่าให้เด็กฟัง::Grandfather tells an old story to the child.|ฉันไปบ้านตากับแม่::I go to grandfather's house with mother.|ตาชอบดื่มชาร้อน::Grandfather likes drinking hot tea.
ยาย|maternal grandmother|family noun|ยายทำซุปอร่อย::Grandmother makes tasty soup.|เด็กช่วยยายถือถุง::The child helps grandmother carry a bag.|ยายอยู่บ้านหลังเล็ก::Grandmother lives in a small house.
สามี|husband|family noun|สามีของเธอเป็นครู::Her husband is a teacher.|สามีช่วยทำอาหารเย็น::The husband helps make dinner.|สามีไปทำงานแต่เช้า::The husband goes to work early.
ภรรยา|wife|family noun|ภรรยาของเขาเป็นหมอ::His wife is a doctor.|ภรรยาซื้อผลไม้ที่ตลาด::The wife buys fruit at the market.|ภรรยานั่งอ่านหนังสือ::The wife sits and reads a book.
อาหาร|food|noun|อาหารอยู่บนโต๊ะ::The food is on the table.|ร้านนี้ขายอาหารไทย::This shop sells Thai food.|แม่ทำอาหารให้ครอบครัว::Mother makes food for the family.
อาหารเช้า|breakfast|noun|อาหารเช้าวันนี้มีไข่::Breakfast today has eggs.|ฉันกินอาหารเช้าก่อนเรียน::I eat breakfast before class.|แม่เตรียมอาหารเช้าให้เด็ก::Mother prepares breakfast for the child.
อาหารกลางวัน|lunch|noun|อาหารกลางวันอยู่ในกล่อง::Lunch is in the box.|เรากินอาหารกลางวันที่โรงเรียน::We eat lunch at school.|ครูซื้ออาหารกลางวันง่ายๆ::The teacher buys a simple lunch.
เนื้อ|meat|noun|เนื้ออยู่ในตู้เย็น::The meat is in the refrigerator.|แม่ทำเนื้อกับผัก::Mother cooks meat with vegetables.|ร้านนี้ขายเนื้อสด::This shop sells fresh meat.
หมู|pork pig|noun|หมูอยู่ในซุป::Pork is in the soup.|แม่ซื้อหมูที่ตลาด::Mother buys pork at the market.|ร้านอาหารนี้มีข้าวหมู::This restaurant has pork with rice.
ซุป|soup|noun|ซุปร้อนอยู่ในถ้วย::Hot soup is in the bowl.|เด็กกินซุปกับขนมปัง::The child eats soup with bread.|แม่ทำซุปผักตอนเย็น::Mother makes vegetable soup in the evening.
ก๋วยเตี๋ยว|noodles|noun|ก๋วยเตี๋ยวร้อนมาก::The noodles are very hot.|ฉันกินก๋วยเตี๋ยวที่ร้าน::I eat noodles at the shop.|พ่อซื้อก๋วยเตี๋ยวให้ลูก::Father buys noodles for the child.
น้ำปลา|fish sauce|noun|น้ำปลาอยู่ข้างเกลือ::The fish sauce is beside the salt.|แม่ใส่น้ำปลาในซุป::Mother puts fish sauce in the soup.|ร้านขายน้ำปลาและน้ำตาล::The shop sells fish sauce and sugar.
พริก|chili|noun|พริกสีแดงเผ็ดมาก::The red chili is very spicy.|แม่ซื้อพริกที่ตลาด::Mother buys chilies at the market.|ฉันไม่ใส่พริกในข้าว::I do not put chili in rice.
มะนาว|lime|noun|มะนาวอยู่ในถุงผัก::The lime is in the vegetable bag.|แม่ใส่มะนาวในน้ำปลา::Mother puts lime in the fish sauce.|น้ำมะนาวเปรี้ยวและเย็น::Lime juice is sour and cold.
ส้ม|orange|noun|ส้มลูกนี้หวานมาก::This orange is very sweet.|เด็กกินส้มหลังอาหาร::The child eats an orange after food.|แม่ซื้อส้มเจ็ดลูก::Mother buys seven oranges.
มะม่วง|mango|noun|มะม่วงสีเหลืองอยู่บนจาน::The yellow mango is on the plate.|ฉันชอบมะม่วงหวาน::I like sweet mangoes.|ตลาดมีมะม่วงสดวันนี้::The market has fresh mangoes today.
แตงโม|watermelon|noun|แตงโมลูกใหญ่เย็นมาก::The big watermelon is very cold.|เด็กกินแตงโมในสวน::The child eats watermelon in the park.|แม่ซื้อแตงโมให้ครอบครัว::Mother buys a watermelon for the family.
องุ่น|grapes|noun|องุ่นอยู่ในตู้เย็น::The grapes are in the refrigerator.|ฉันซื้อองุ่นหนึ่งถุง::I buy one bag of grapes.|เด็กชอบองุ่นหวาน::The child likes sweet grapes.
ข้าวโพด|corn|noun|ข้าวโพดร้อนอยู่บนจาน::Hot corn is on the plate.|แม่ซื้อข้าวโพดที่ตลาด::Mother buys corn at the market.|เรากินข้าวโพดกับซุป::We eat corn with soup.
มันฝรั่ง|potato|noun|มันฝรั่งอยู่ในถุง::The potato is in the bag.|แม่ทำซุปมันฝรั่ง::Mother makes potato soup.|เด็กกินมันฝรั่งกับไก่::The child eats potato with chicken.
มะเขือเทศ|tomato|noun|มะเขือเทศสีแดงสด::The tomato is fresh and red.|ฉันใส่มะเขือเทศในซุป::I put tomato in the soup.|ตลาดขายมะเขือเทศถูก::The market sells cheap tomatoes.
ถั่ว|beans nuts|noun|ถั่วอยู่ในถ้วยเล็ก::Beans are in the small bowl.|แม่ซื้อถั่วให้เด็ก::Mother buys nuts for the child.|ฉันกินถั่วกับข้าว::I eat beans with rice.
ขนม|snack sweet|noun|ขนมอยู่ในกล่อง::The snack is in the box.|เด็กซื้อขนมที่ร้าน::The child buys a snack at the shop.|แม่ให้ขนมกับน้อง::Mother gives a snack to my younger sibling.
ไอศกรีม|ice cream|noun|ไอศกรีมเย็นและหวาน::The ice cream is cold and sweet.|เด็กกินไอศกรีมวันเสาร์::The child eats ice cream on Saturday.|ร้านนี้ขายไอศกรีมมะม่วง::This shop sells mango ice cream.
น้ำผลไม้|fruit juice|noun|น้ำผลไม้อยู่ในแก้ว::Fruit juice is in the glass.|ฉันดื่มน้ำผลไม้ตอนเช้า::I drink fruit juice in the morning.|เด็กซื้อน้ำผลไม้เย็น::The child buys cold fruit juice.
น้ำอัดลม|soda|noun|น้ำอัดลมอยู่ในตู้เย็น::The soda is in the refrigerator.|ฉันไม่ดื่มน้ำอัดลมตอนเช้า::I do not drink soda in the morning.|ร้านขายน้ำอัดลมหลายชนิด::The shop sells many kinds of soda.
รส|taste flavor|noun|รสของซุปเค็มไป::The soup's taste is too salty.|ฉันชอบรสหวาน::I like a sweet taste.|น้ำผลไม้นี้มีรสมะม่วง::This fruit juice has mango flavor.
อร่อย|delicious|adjective|อาหารนี้อร่อยมาก::This food is very delicious.|แม่ทำซุปอร่อย::Mother makes delicious soup.|ร้านอาหารมีข้าวอร่อย::The restaurant has delicious rice.
หวาน|sweet|adjective|มะม่วงลูกนี้หวาน::This mango is sweet.|ชาแก้วนี้หวานมาก::This glass of tea is very sweet.|เด็กชอบขนมหวาน::The child likes sweet snacks.
เปรี้ยว|sour|adjective|มะนาวเปรี้ยวมาก::The lime is very sour.|น้ำผลไม้นี้ไม่เปรี้ยว::This fruit juice is not sour.|ฉันกินมะม่วงเปรี้ยวกับเกลือ::I eat sour mango with salt.
เค็ม|salty|adjective|ซุปนี้เค็มไป::This soup is too salty.|ปลาเค็มอยู่บนจาน::The salty fish is on the plate.|แม่ใส่เกลือน้อยเพราะไม่ชอบเค็ม::Mother puts little salt because she does not like salty food.
เผ็ด|spicy|adjective|พริกแดงเผ็ดมาก::Red chilies are very spicy.|ฉันไม่กินอาหารเผ็ด::I do not eat spicy food.|ซุปนี้เผ็ดนิดหน่อย::This soup is a little spicy.
ขม|bitter|adjective|กาแฟดำขมนิดหน่อย::Black coffee is a little bitter.|ยาเม็ดนี้ขมมาก::This pill is very bitter.|เด็กไม่ชอบรสขม::The child does not like bitter taste.
สด|fresh|adjective|ผักสดอยู่ในตลาด::Fresh vegetables are in the market.|ปลาสดราคาไม่แพง::Fresh fish is not expensive.|แม่ซื้อนมสดหนึ่งขวด::Mother buys one bottle of fresh milk.
สะอาด|clean|adjective|ห้องน้ำสะอาดมาก::The bathroom is very clean.|จานสะอาดอยู่ในตู้::The clean plates are in the cabinet.|โรงแรมนี้สะอาดและเงียบ::This hotel is clean and quiet.
สกปรก|dirty|adjective|รองเท้าสกปรกอยู่หน้าบ้าน::The dirty shoes are in front of the house.|เด็กล้างมือที่สกปรก::The child washes dirty hands.|พื้นห้องไม่สกปรกแล้ว::The room floor is not dirty now.
ปลอดภัย|safe|adjective|ถนนนี้ปลอดภัยตอนกลางวัน::This road is safe during the day.|เด็กอยู่ในที่ปลอดภัย::The child is in a safe place.|คนขับขับรถอย่างปลอดภัย::The driver drives safely.
อันตราย|dangerous|adjective|ถนนเปียกอันตรายมาก::The wet road is very dangerous.|อย่าเล่นใกล้ไฟเพราะอันตราย::Do not play near fire because it is dangerous.|มีดคมอันตรายสำหรับเด็ก::A sharp knife is dangerous for children.
เปิด|open turn on|verb adjective|ร้านเปิดตอนเช้า::The shop opens in the morning.|ฉันเปิดหน้าต่างรับลม::I open the window for air.|ไฟในห้องเปิดอยู่::The light in the room is on.
ปิด|close turn off|verb adjective|ร้านปิดวันพุธ::The shop is closed on Wednesday.|กรุณาปิดประตูก่อนนอน::Please close the door before sleeping.|แม่ปิดไฟในครัว::Mother turns off the kitchen light.
เต็ม|full|adjective|แก้วน้ำเต็มแล้ว::The water glass is full now.|รถเมล์เต็มตอนเช้า::The bus is full in the morning.|กล่องนี้เต็มไปด้วยหนังสือ::This box is full of books.
เบา|light soft|adjective adverb|กระเป๋าใบนี้เบามาก::This bag is very light.|ครูพูดเสียงเบา::The teacher speaks softly.|ลมเบาพัดเข้าห้อง::A light wind blows into the room.
หนัก|heavy|adjective|กล่องนี้หนักมาก::This box is very heavy.|กระเป๋าของพ่อหนัก::Father's bag is heavy.|เด็กถือจานหนักไม่ได้::The child cannot carry the heavy plate.
ยาว|long|adjective|ถนนนี้ยาวมาก::This road is very long.|ผมของเธอยาว::Her hair is long.|บทเรียนวันนี้ไม่ยาว::Today's lesson is not long.
สั้น|short|adjective|กางเกงสั้นอยู่ในตู้::The shorts are in the closet.|ประโยคนี้สั้นและง่าย::This sentence is short and easy.|ผมของเด็กสั้นมาก::The child's hair is very short.
สูง|tall high|adjective|ภูเขาสูงอยู่ไกล::The high mountain is far away.|พี่ชายของฉันสูง::My older brother is tall.|ตึกสูงอยู่ในเมือง::The tall building is in the city.
ต่ำ|low|adjective|โต๊ะตัวนี้ต่ำ::This table is low.|เสียงของเขาต่ำมาก::His voice is very low.|ราคาต่ำกว่าร้านอื่น::The price is lower than other shops.
กว้าง|wide|adjective|ถนนนี้กว้างและสะอาด::This road is wide and clean.|ห้องเรียนกว้างมาก::The classroom is very wide.|ประตูใหญ่กว้างพอ::The big door is wide enough.
แคบ|narrow|adjective|ทางนี้แคบมาก::This way is very narrow.|ห้องน้ำในบ้านแคบ::The bathroom in the house is narrow.|ถนนแคบมีรถน้อย::The narrow road has few cars.
แดง|red|color adjective|เสื้อแดงอยู่บนเตียง::The red shirt is on the bed.|ไฟแดงอยู่หน้ารถ::The red light is in front of the car.|เด็กถือร่มแดง::The child carries a red umbrella.
ดำ|black|color adjective|กาแฟดำอยู่ในแก้ว::Black coffee is in the glass.|รองเท้าดำของพ่อใหม่::Father's black shoes are new.|แมวดำนอนใต้โต๊ะ::The black cat sleeps under the table.
ขาว|white|color adjective|เสื้อขาวอยู่ในตู้::The white shirt is in the closet.|ข้าวขาวอยู่ในจาน::White rice is on the plate.|หมวกขาวของเด็กสวย::The child's white hat is beautiful.
เขียว|green|color adjective|ผักเขียวสดมาก::The green vegetables are very fresh.|ฉันชอบสีเขียว::I like green.|กระเป๋าเขียวอยู่บนเก้าอี้::The green bag is on the chair.
เหลือง|yellow|color adjective|กล้วยเหลืองอยู่บนจาน::The yellow banana is on the plate.|เสื้อเหลืองของแม่ใหม่::Mother's yellow shirt is new.|ไฟเหลืองอยู่หลังไฟเขียว::The yellow light is after the green light.
น้ำเงิน|blue|color adjective|กระเป๋าน้ำเงินอยู่ในห้อง::The blue bag is in the room.|เขาใส่เสื้อน้ำเงิน::He wears a blue shirt.|ปากกาน้ำเงินอยู่บนโต๊ะ::The blue pen is on the table.
สี|color|noun|สีนี้สวยมาก::This color is very beautiful.|ฉันชอบสีเขียว::I like the color green.|เด็กวาดรูปด้วยสีแดง::The child draws a picture with red color.
กลม|round|adjective|โต๊ะกลมอยู่ในครัว::The round table is in the kitchen.|ส้มลูกนี้กลมมาก::This orange is very round.|เด็กวาดวงกลมในสมุด::The child draws a circle in the notebook.
โค้ง|curved bend|adjective noun|ถนนโค้งไปทางซ้าย::The road curves to the left.|สะพานนี้โค้งสวย::This bridge has a beautiful curve.|รถขับช้าที่ทางโค้ง::The car drives slowly at the curve.
แห้ง|dry|adjective|เสื้อแห้งแล้วบนระเบียง::The shirt is dry now on the balcony.|ถนนแห้งหลังฝนหยุด::The road is dry after the rain stops.|ขนมปังแห้งไม่อร่อย::Dry bread is not delicious.
เปียก|wet|adjective|รองเท้าเปียกเพราะฝนตก::The shoes are wet because it rains.|พื้นห้องน้ำเปียก::The bathroom floor is wet.|ผมของเด็กเปียกหลังว่ายน้ำ::The child's hair is wet after swimming.
มืด|dark|adjective|ห้องนี้มืดตอนกลางคืน::This room is dark at night.|ถนนมืดไม่มีไฟ::The road is dark and has no lights.|ฉันไม่อ่านหนังสือในที่มืด::I do not read in a dark place.
สว่าง|bright|adjective|ห้องเรียนสว่างตอนเช้า::The classroom is bright in the morning.|ไฟสว่างมากในครัว::The light is very bright in the kitchen.|หน้าต่างใหญ่ทำให้ห้องสว่าง::The big window makes the room bright.
เงียบ|quiet|adjective|ห้องสมุดเงียบมาก::The library is very quiet.|ตอนกลางคืนถนนเงียบ::At night the road is quiet.|เด็กนั่งเงียบในห้อง::The child sits quietly in the room.
ดัง|loud|adjective|เสียงรถดังมาก::The car sound is very loud.|โทรศัพท์ดังตอนเช้า::The phone rings in the morning.|อย่าพูดดังในห้องสมุด::Do not speak loudly in the library.
สนุก|fun|adjective|บทเรียนวันนี้สนุก::Today's lesson is fun.|เด็กเล่นเกมสนุกมาก::The child plays a very fun game.|การเดินทางไปทะเลสนุก::The trip to the sea is fun.
น่าเบื่อ|boring|adjective|หนังเรื่องนี้น่าเบื่อ::This movie is boring.|งานนี้ไม่น่าเบื่อสำหรับฉัน::This work is not boring for me.|เขาคิดว่าการรอนานน่าเบื่อ::He thinks waiting a long time is boring.
เหนื่อย|tired|adjective|เขาเหนื่อยหลังวิ่ง::He is tired after running.|แม่เหนื่อยจากงานบ้าน::Mother is tired from housework.|ฉันเดินไกลจึงเหนื่อย::I walked far, so I am tired.
หิว|hungry|adjective|เด็กหิวตอนเที่ยง::The child is hungry at noon.|ฉันหิวหลังเรียน::I am hungry after class.|ถ้าคุณหิวเรากินข้าว::If you are hungry, we eat rice.
อิ่ม|full not hungry|adjective|ฉันอิ่มหลังอาหารเย็น::I am full after dinner.|เด็กอิ่มแล้วไม่กินขนม::The child is full and does not eat snacks.|เขาดื่มนมแล้วอิ่ม::He drinks milk and is full.
กระหาย|thirsty|adjective|ฉันกระหายน้ำหลังวิ่ง::I am thirsty after running.|เด็กกระหายเพราะอากาศร้อน::The child is thirsty because the weather is hot.|ถ้ากระหายให้ดื่มน้ำ::If thirsty, drink water.
ง่วง|sleepy|adjective|น้องง่วงตอนกลางคืน::My younger sibling is sleepy at night.|ฉันง่วงหลังอาหารกลางวัน::I am sleepy after lunch.|เด็กง่วงและอยากนอน::The child is sleepy and wants to sleep.
สบาย|comfortable well|adjective|วันนี้ฉันสบายดี::Today I am well.|ห้องนี้สบายและเงียบ::This room is comfortable and quiet.|เก้าอี้ตัวนี้นั่งสบาย::This chair is comfortable to sit in.
ไม่สบาย|sick unwell|adjective|วันนี้แม่ไม่สบาย::Mother is sick today.|เด็กไม่สบายจึงอยู่บ้าน::The child is sick, so stays home.|ถ้าไม่สบายควรพัก::If you are sick, you should rest.
ดีใจ|happy glad|adjective|เด็กดีใจเมื่อเห็นแม่::The child is happy when seeing mother.|ฉันดีใจที่ได้หนังสือใหม่::I am glad to get a new book.|พ่อดีใจเพราะลูกกลับบ้าน::Father is happy because the child comes home.
เสียใจ|sad sorry|adjective|เธอเสียใจเพราะทำแก้วแตก::She is sad because she broke a glass.|ฉันเสียใจที่มาช้า::I am sorry that I came late.|เด็กเสียใจเมื่อฝนตก::The child is sad when it rains.
กลัว|afraid|adjective verb|เด็กกลัวความมืด::The child is afraid of the dark.|ฉันไม่กลัวหมาเล็ก::I am not afraid of small dogs.|เขากลัวเสียงดัง::He is afraid of loud sounds.
โกรธ|angry|adjective|แม่ไม่โกรธเด็ก::Mother is not angry at the child.|เขาโกรธเพราะรถมาช้า::He is angry because the bus came late.|อย่าพูดดังเมื่อครูโกรธ::Do not speak loudly when the teacher is angry.
ยิ้ม|smile|verb noun|เด็กยิ้มให้ครู::The child smiles at the teacher.|แม่ยิ้มเมื่อเห็นลูก::Mother smiles when she sees the child.|เขายิ้มและพูดขอบคุณ::He smiles and says thank you.
หัวเราะ|laugh|verb|เด็กหัวเราะในสวน::The child laughs in the park.|เราหัวเราะกับเพื่อน::We laugh with friends.|ครูหัวเราะเบาๆ::The teacher laughs softly.
ร้องไห้|cry|verb|น้องร้องไห้เพราะหิว::My younger sibling cries because of hunger.|เด็กไม่ร้องไห้แล้ว::The child is not crying now.|แม่ปลอบลูกที่ร้องไห้::Mother comforts the crying child.
ปวด|hurt ache|verb adjective|ฉันปวดหัวตอนเช้า::I have a headache in the morning.|พ่อปวดเท้าหลังเดินไกล::Father's foot hurts after walking far.|ถ้าปวดท้องให้บอกแม่::If your stomach hurts, tell mother.
หัว|head|noun|หัวของเด็กเปียก::The child's head is wet.|ฉันปวดหัววันนี้::I have a headache today.|หมวกอยู่บนหัวพ่อ::The hat is on father's head.
ใบหน้า|face|noun|ใบหน้าของเธอสวย::Her face is beautiful.|เด็กล้างใบหน้าตอนเช้า::The child washes the face in the morning.|รอยยิ้มอยู่บนใบหน้าแม่::A smile is on mother's face.
ดวงตา|eyes|noun|ดวงตาของเด็กสดใส::The child's eyes are bright.|แม่มีดวงตาสวย::Mother has beautiful eyes.|อย่าอ่านหนังสือในที่มืดเพราะดวงตาจะเหนื่อย::Do not read in the dark because your eyes will get tired.
หู|ear|noun|หูของฉันได้ยินเสียงรถ::My ear hears the car sound.|เด็กปิดหูเพราะเสียงดัง::The child covers ears because the sound is loud.|หมอถามว่าหูเจ็บไหม::The doctor asks if the ear hurts.
ปาก|mouth|noun|ปากของเด็กมีขนม::The child's mouth has a snack.|กรุณาปิดปากเมื่อไอ::Please cover your mouth when coughing.|แม่ล้างปากให้น้อง::Mother washes the younger child's mouth.
ฟัน|tooth teeth|noun|ฟันของเด็กขาว::The child's teeth are white.|ฉันแปรงฟันทุกเช้า::I brush my teeth every morning.|หมอดูฟันของฉัน::The doctor looks at my teeth.
มือ|hand|noun|มือของแม่อุ่น::Mother's hand is warm.|เด็กล้างมือก่อนกินข้าว::The child washes hands before eating.|ฉันถือแก้วด้วยมือซ้าย::I hold the glass with my left hand.
เท้า|foot feet|noun|เท้าของพ่อเปียกฝน::Father's feet are wet from rain.|เด็กใส่รองเท้าที่เท้า::The child puts shoes on the feet.|ฉันปวดเท้าหลังเดินนาน::My feet hurt after walking a long time.
ท้อง|stomach belly|noun|ท้องของเด็กหิวมาก::The child's stomach is very hungry.|ฉันปวดท้องหลังอาหาร::My stomach hurts after food.|แม่ถามว่าท้องยังเจ็บไหม::Mother asks if the stomach still hurts.
หลัง|back behind|noun preposition|หลังบ้านมีต้นไม้ใหญ่::Behind the house there is a big tree.|ฉันปวดหลังจากนั่งนาน::My back hurts from sitting a long time.|เด็กยืนหลังครู::The child stands behind the teacher.
เส้นผม|hair strand|noun|เส้นผมของเธอยาวมาก::Her hair is very long.|แม่หวีเส้นผมให้น้อง::Mother combs the younger child's hair.|เส้นผมเปียกหลังอาบน้ำ::The hair is wet after bathing.
อากาศ|weather air|noun|อากาศวันนี้ดีมาก::The weather today is very good.|ตอนเช้าอากาศเย็น::In the morning the weather is cool.|อากาศร้อนทำให้ฉันกระหาย::Hot weather makes me thirsty.
ลม|wind|noun|ลมเย็นพัดเข้าห้อง::A cool wind blows into the room.|วันนี้มีลมแรง::Today there is strong wind.|ฉันเปิดหน้าต่างรับลม::I open the window for air.
เมฆ|cloud|noun|เมฆดำอยู่บนฟ้า::Dark clouds are in the sky.|วันนี้มีเมฆมาก::Today there are many clouds.|เด็กวาดเมฆในสมุด::The child draws clouds in the notebook.
ฟ้า|sky|noun|ฟ้าวันนี้สวยมาก::The sky today is very beautiful.|นกบินบนฟ้า::Birds fly in the sky.|เมฆอยู่เต็มฟ้า::Clouds fill the sky.
ดาว|star|noun|ดาวสว่างบนฟ้า::Stars are bright in the sky.|คืนนี้ฉันดูดาวกับพ่อ::Tonight I look at stars with father.|เด็กวาดดาวสีเหลือง::The child draws a yellow star.
พระอาทิตย์|sun|noun|พระอาทิตย์ขึ้นตอนเช้า::The sun rises in the morning.|วันนี้พระอาทิตย์แรงมาก::The sun is very strong today.|เด็กวาดพระอาทิตย์บนกระดาษ::The child draws the sun on paper.
พระจันทร์|moon|noun|พระจันทร์สวยคืนนี้::The moon is beautiful tonight.|เด็กมองพระจันทร์จากหน้าต่าง::The child looks at the moon from the window.|พระจันทร์อยู่บนฟ้า::The moon is in the sky.
ต้นไม้|tree|noun|ต้นไม้อยู่หน้าบ้าน::The tree is in front of the house.|เด็กนั่งใต้ต้นไม้::The child sits under the tree.|สวนนี้มีต้นไม้ใหญ่หลายต้น::This park has many big trees.
ดอกไม้|flower|noun|ดอกไม้สีแดงอยู่ในสวน::Red flowers are in the park.|แม่ซื้อดอกไม้ให้ยาย::Mother buys flowers for grandmother.|เด็กวาดดอกไม้สวย::The child draws a beautiful flower.
ใบไม้|leaf|noun|ใบไม้สีเขียวอยู่บนพื้น::Green leaves are on the ground.|ลมพัดใบไม้เข้าบ้าน::The wind blows leaves into the house.|เด็กเก็บใบไม้ในสวน::The child collects leaves in the park.
สุนัข|dog|noun|สุนัขนอนใต้โต๊ะ::The dog sleeps under the table.|เด็กเล่นกับสุนัขในสวน::The child plays with a dog in the park.|สุนัขสีดำวิ่งเร็ว::The black dog runs fast.
แมว|cat|noun|แมวนอนบนเตียง::The cat sleeps on the bed.|เด็กให้นมแมว::The child gives milk to the cat.|แมวขาวอยู่หน้าบ้าน::The white cat is in front of the house.
นก|bird|noun|นกบินบนฟ้า::The bird flies in the sky.|เด็กดูนกในสวน::The child watches birds in the park.|นกร้องตอนเช้า::The bird sings in the morning.
ม้า|horse|noun|ม้าวิ่งในสนาม::The horse runs in the field.|เด็กดูม้าจากไกลๆ::The child watches the horse from far away.|ม้าสีน้ำตาลกินหญ้า::The brown horse eats grass.
วัว|cow|noun|วัวอยู่ในทุ่ง::The cow is in the field.|ชาวนาดูแลวัวตอนเช้า::The farmer takes care of the cow in the morning.|เด็กเห็นวัวใกล้หมู่บ้าน::The child sees a cow near the village.
ช้าง|elephant|noun|ช้างตัวใหญ่อยู่ในรูป::The big elephant is in the picture.|เด็กชอบดูช้าง::The child likes watching elephants.|ช้างเดินช้าๆในสวนสัตว์::The elephant walks slowly in the zoo.
เป็ด|duck|noun|เป็ดว่ายน้ำในบ่อ::The duck swims in the pond.|เด็กให้อาหารเป็ด::The child feeds the duck.|เป็ดสีขาวเดินข้างน้ำ::The white duck walks beside the water.
ไข่ดาว|fried egg|noun|ไข่ดาวอยู่บนข้าว::The fried egg is on the rice.|แม่ทำไข่ดาวตอนเช้า::Mother makes a fried egg in the morning.|เด็กกินไข่ดาวกับขนมปัง::The child eats a fried egg with bread.
บทเรียน|lesson|noun|บทเรียนวันนี้ง่าย::Today's lesson is easy.|ครูเริ่มบทเรียนตอนเก้าโมง::The teacher starts the lesson at nine.|นักเรียนอ่านบทเรียนใหม่::The student reads the new lesson.
การบ้าน|homework|noun|การบ้านอยู่ในสมุด::The homework is in the notebook.|เด็กทำการบ้านบนโต๊ะ::The child does homework on the table.|ครูตรวจการบ้านตอนเช้า::The teacher checks homework in the morning.
คำถาม|question|noun|คำถามนี้ง่ายมาก::This question is very easy.|นักเรียนถามคำถามกับครู::The student asks the teacher a question.|ครูเขียนคำถามบนกระดาน::The teacher writes the question on the board.
คำตอบ|answer|noun|คำตอบของคุณถูก::Your answer is correct.|เด็กเขียนคำตอบในสมุด::The child writes the answer in the notebook.|ครูอ่านคำตอบช้าๆ::The teacher reads the answer slowly.
คะแนน|score points|noun|คะแนนของฉันดีขึ้น::My score is better.|นักเรียนดูคะแนนในสมุด::The student looks at the score in the notebook.|ครูให้คะแนนหลังสอบ::The teacher gives scores after the test.
สอบ|exam test|verb noun|วันนี้นักเรียนสอบภาษาไทย::Today the students take a Thai test.|ฉันอ่านหนังสือก่อนสอบ::I read a book before the exam.|ครูบอกว่าสอบไม่ยาก::The teacher says the test is not difficult.
ภาษา|language|noun|ภาษาไทยสวยมาก::The Thai language is very beautiful.|ฉันเรียนภาษากับครู::I study language with a teacher.|เด็กพูดได้สองภาษา::The child can speak two languages.
ภาษาไทย|Thai language|noun|ภาษาไทยมีเสียงสวย::The Thai language has beautiful sounds.|เราเรียนภาษาไทยทุกวัน::We study Thai every day.|ครูพูดภาษาไทยช้าๆ::The teacher speaks Thai slowly.
ภาษาอังกฤษ|English language|noun|ภาษาอังกฤษอยู่ในหนังสือเล่มนี้::English is in this book.|นักเรียนอ่านภาษาอังกฤษได้::The student can read English.|ครูสอนภาษาอังกฤษตอนบ่าย::The teacher teaches English in the afternoon.
ชื่อ|name|noun|ชื่อของฉันสั้น::My name is short.|คุณเขียนชื่อบนกระดาษ::You write your name on the paper.|ครูถามชื่อของนักเรียน::The teacher asks the student's name.
นามสกุล|surname|noun|นามสกุลของเขายาว::His surname is long.|ฉันเขียนนามสกุลบนตั๋ว::I write my surname on the ticket.|ครูอ่านนามสกุลนักเรียน::The teacher reads the student's surname.
ประเทศ|country|noun|ประเทศของฉันอยู่ไกล::My country is far away.|เขามาจากประเทศเล็ก::He comes from a small country.|เราเรียนชื่อประเทศในห้อง::We learn country names in the room.
จังหวัด|province|noun|จังหวัดนี้มีทะเลสวย::This province has a beautiful sea.|พ่อทำงานในจังหวัดใกล้บ้าน::Father works in a province near home.|เราไปจังหวัดใหม่วันเสาร์::We go to a new province on Saturday.
หมู่บ้าน|village|noun|หมู่บ้านอยู่ใกล้ภูเขา::The village is near the mountain.|ชาวนาอยู่ในหมู่บ้านเล็ก::The farmer lives in a small village.|เด็กเดินผ่านหมู่บ้าน::The child walks through the village.
เพลง|song|noun|เพลงนี้สนุกมาก::This song is very fun.|ฉันฟังเพลงตอนเย็น::I listen to music in the evening.|เด็กร้องเพลงกับครู::The child sings a song with the teacher.
รูป|picture photo|noun|รูปของครอบครัวอยู่บนโต๊ะ::The family photo is on the table.|เด็กวาดรูปดอกไม้::The child draws a flower picture.|ฉันถ่ายรูปที่ทะเล::I take a photo at the sea.
ภาพ|image picture|noun|ภาพนี้สวยมาก::This picture is very beautiful.|ครูให้ดูภาพบนกระดาน::The teacher shows a picture on the board.|เด็กวาดภาพบ้านเล็ก::The child draws a picture of a small house.
ข่าว|news|noun|พ่อฟังข่าวตอนเช้า::Father listens to the news in the morning.|ข่าววันนี้พูดเรื่องฝน::Today's news talks about rain.|แม่อ่านข่าวในโทรศัพท์::Mother reads the news on the phone.
งาน|work job|noun|งานของพ่อง่ายวันนี้::Father's work is easy today.|ฉันมีงานที่บ้าน::I have work at home.|ครูตรวจงานนักเรียน::The teacher checks the student's work.
งานบ้าน|housework|noun|งานบ้านวันนี้มีมาก::There is a lot of housework today.|ฉันช่วยแม่ทำงานบ้าน::I help mother do housework.|พี่ทำงานบ้านตอนเย็น::My older sibling does housework in the evening.
ประชุม|meeting|verb noun|พ่อมีประชุมตอนเช้า::Father has a meeting in the morning.|ครูประชุมหลังเลิกเรียน::The teacher has a meeting after class.|การประชุมเริ่มเก้าโมง::The meeting starts at nine o'clock.
พนักงาน|employee staff|noun|พนักงานร้านพูดสุภาพ::The shop employee speaks politely.|พนักงานโรงแรมช่วยเรา::The hotel employee helps us.|พนักงานขายตั๋วอยู่ที่สถานี::The ticket employee is at the station.
ลูกค้า|customer|noun|ลูกค้าอยู่ในร้านกาแฟ::The customer is in the coffee shop.|พนักงานช่วยลูกค้าเลือกของ::The employee helps the customer choose an item.|วันนี้ร้านมีลูกค้ามาก::Today the shop has many customers.
หัวหน้า|boss leader|noun|หัวหน้าพูดกับพนักงาน::The boss speaks with the employee.|หัวหน้าอยู่ในสำนักงาน::The boss is in the office.|เขารอหัวหน้าที่ที่ทำงาน::He waits for the boss at work.
เพื่อนบ้าน|neighbor|noun|เพื่อนบ้านของฉันใจดี::My neighbor is kind.|แม่คุยกับเพื่อนบ้านตอนเย็น::Mother talks with the neighbor in the evening.|เพื่อนบ้านช่วยถือถุง::The neighbor helps carry the bag.
ราคา|price|noun|ราคากาแฟไม่แพง::The coffee price is not expensive.|ฉันถามราคากระเป๋า::I ask the price of the bag.|ร้านนี้เขียนราคาบนป้าย::This shop writes the price on the sign.
รายการ|list program|noun|รายการอาหารอยู่บนโต๊ะ::The menu list is on the table.|แม่เขียนรายการซื้อของ::Mother writes a shopping list.|ฉันดูรายการในโทรศัพท์::I look at the list on the phone.
เมนู|menu|noun|เมนูร้านนี้มีรูป::This shop's menu has pictures.|เขาอ่านเมนูก่อนสั่งอาหาร::He reads the menu before ordering food.|พนักงานให้เมนูกับลูกค้า::The employee gives the menu to the customer.
ใบเสร็จ|receipt|noun|ใบเสร็จอยู่ในกระเป๋า::The receipt is in the bag.|พนักงานให้ใบเสร็จหลังจ่ายเงิน::The employee gives a receipt after payment.|แม่เก็บใบเสร็จจากร้าน::Mother keeps the receipt from the shop.
คิว|queue line|noun|คิวที่ธนาคารยาวมาก::The queue at the bank is very long.|ฉันรอคิวซื้อขนมปัง::I wait in line to buy bread.|ลูกค้ายืนในคิวอย่างเงียบ::The customer stands quietly in the queue.
อีเมล|email|noun|อีเมลจากครูอยู่ในโทรศัพท์::The email from the teacher is on the phone.|ฉันเขียนอีเมลถึงเพื่อน::I write an email to a friend.|พ่ออ่านอีเมลตอนเช้า::Father reads email in the morning.
เอา|take want|verb|ฉันเอาหนังสือใส่กระเป๋า::I put the book into the bag.|แม่เอาผักจากตู้เย็น::Mother takes vegetables from the refrigerator.|คุณเอาชาหรือกาแฟ::Do you want tea or coffee?
ใส่|put in wear|verb|ฉันใส่น้ำแข็งในแก้ว::I put ice in the glass.|เด็กใส่รองเท้าก่อนออกบ้าน::The child puts on shoes before leaving home.|แม่ใส่เกลือในซุป::Mother puts salt in the soup.
วาง|put place|verb|พ่อวางกุญแจบนโต๊ะ::Father puts the key on the table.|ฉันวางหนังสือข้างเตียง::I put the book beside the bed.|เด็กวางจานในครัว::The child puts the plate in the kitchen.
ถือ|hold carry|verb|เด็กถือร่มสีแดง::The child carries a red umbrella.|ฉันถือถุงผลไม้::I carry a bag of fruit.|แม่ถือแก้วน้ำให้พ่อ::Mother holds a glass of water for father.
หยิบ|pick up|verb|ฉันหยิบปากกาจากโต๊ะ::I pick up a pen from the table.|แม่หยิบไข่จากตู้เย็น::Mother takes eggs from the refrigerator.|เด็กหยิบหนังสือให้ครู::The child picks up a book for the teacher.
หา|look for|verb|ฉันหากุญแจในกระเป๋า::I look for the key in the bag.|พ่อหาร้านอาหารใกล้โรงแรม::Father looks for a restaurant near the hotel.|เด็กหาสมุดบนโต๊ะ::The child looks for a notebook on the table.
เจอ|find meet|verb|ฉันเจอกระเป๋าใต้โต๊ะ::I found the bag under the table.|เราเจอครูที่ตลาด::We meet the teacher at the market.|เด็กเจอแมวหน้าบ้าน::The child finds a cat in front of the house.
รอ|wait|verb|ฉันรอรถเมล์ที่ป้าย::I wait for the bus at the stop.|แม่รอพ่อหน้าร้าน::Mother waits for father in front of the shop.|เด็กรอครูในห้องเรียน::The child waits for the teacher in the classroom.
ขึ้น|go up get on|verb|ฉันขึ้นรถไฟที่สถานี::I get on the train at the station.|เด็กขึ้นบันไดช้าๆ::The child goes up the stairs slowly.|พระอาทิตย์ขึ้นตอนเช้า::The sun rises in the morning.
ลง|go down get off|verb|เราลงรถเมล์หน้าตลาด::We get off the bus in front of the market.|เด็กลงบันไดอย่างระวัง::The child goes down the stairs carefully.|เขาลงจากรถไฟที่สถานี::He gets off the train at the station.
เข้า|enter|verb|นักเรียนเข้าโรงเรียนตอนเช้า::The student enters the school in the morning.|ฉันเข้าไปในร้านกาแฟ::I go into the coffee shop.|แมวเข้าห้องนอน::The cat enters the bedroom.
ออก|leave go out|verb|พ่อออกจากบ้านเจ็ดโมง::Father leaves home at seven.|เด็กออกไปเล่นในสวน::The child goes out to play in the park.|เรือออกจากท่าแล้ว::The boat has left the pier.
กลับ|return|verb|แม่กลับบ้านตอนเย็น::Mother returns home in the evening.|ฉันกลับจากโรงเรียนช้า::I return from school late.|พรุ่งนี้พ่อกลับจากเมือง::Tomorrow father returns from the city.
ส่ง|send deliver|verb|ฉันส่งอีเมลให้ครู::I send an email to the teacher.|พ่อส่งลูกไปโรงเรียน::Father sends the child to school.|พนักงานส่งของถึงบ้าน::The employee delivers the item to the house.
รับ|receive pick up|verb|แม่รับลูกที่โรงเรียน::Mother picks up the child at school.|ฉันรับจดหมายจากเพื่อน::I receive a letter from a friend.|พนักงานรับเงินจากลูกค้า::The employee receives money from the customer.
โทร|call phone|verb|ฉันโทรหาแม่ตอนเย็น::I call mother in the evening.|พ่อโทรจากที่ทำงาน::Father calls from work.|ครูโทรบอกว่าเรียนพรุ่งนี้::The teacher calls to say class is tomorrow.
ถาม|ask|verb|นักเรียนถามครูเรื่องการบ้าน::The student asks the teacher about homework.|ฉันถามทางไปสถานี::I ask the way to the station.|แม่ถามว่าหิวไหม::Mother asks if I am hungry.
ตอบ|answer|verb|เด็กตอบคำถามถูก::The child answers the question correctly.|ครูตอบช้าๆให้เราเข้าใจ::The teacher answers slowly so we understand.|ฉันตอบอีเมลตอนเช้า::I answer the email in the morning.
สอน|teach|verb|ครูสอนภาษาไทยทุกวัน::The teacher teaches Thai every day.|แม่สอนลูกทำอาหารง่ายๆ::Mother teaches the child to make simple food.|พี่สอนน้องอ่านหนังสือ::The older sibling teaches the younger sibling to read.
เล่น|play|verb|เด็กเล่นในสนาม::The child plays in the field.|น้องเล่นกับแมวหลังบ้าน::My younger sibling plays with the cat behind the house.|เราเล่นเกมวันเสาร์::We play a game on Saturday.
ร้อง|sing call cry|verb|นกร้องตอนเช้า::Birds sing in the morning.|เด็กร้องเพลงกับครู::The child sings a song with the teacher.|น้องร้องเรียกแม่::My younger sibling calls for mother.
เต้น|dance|verb|เด็กเต้นตามเพลง::The child dances to the song.|เราชอบเต้นในงานเลี้ยง::We like dancing at the party.|ครูสอนเต้นง่ายๆ::The teacher teaches a simple dance.
วาด|draw|verb|เด็กวาดรูปบ้าน::The child draws a house picture.|ฉันวาดดอกไม้สีแดง::I draw a red flower.|ครูวาดแผนที่บนกระดาน::The teacher draws a map on the board.
ล้าง|wash|verb|ฉันล้างมือก่อนกินข้าว::I wash my hands before eating.|แม่ล้างจานในครัว::Mother washes dishes in the kitchen.|เด็กล้างแก้วหลังดื่มนม::The child washes the glass after drinking milk.
เช็ด|wipe|verb|แม่เช็ดโต๊ะหลังอาหาร::Mother wipes the table after food.|ฉันเช็ดมือด้วยผ้า::I wipe my hands with a cloth.|พนักงานเช็ดพื้นร้าน::The employee wipes the shop floor.
ซัก|wash clothes|verb|แม่ซักเสื้อสีขาว::Mother washes the white shirt.|ฉันซักถุงเท้าตอนเย็น::I wash socks in the evening.|เสื้อที่ซักแล้วแห้ง::The washed shirt is dry.
ถอด|take off|verb|เด็กถอดรองเท้าหน้าบ้าน::The child takes off shoes in front of the house.|พ่อถอดหมวกในห้อง::Father takes off his hat in the room.|ฉันถอดแว่นตาก่อนนอน::I take off glasses before sleeping.
ใช้|use|verb|ฉันใช้โทรศัพท์ดูเวลา::I use the phone to check the time.|แม่ใช้มีดหั่นผัก::Mother uses a knife to cut vegetables.|นักเรียนใช้ดินสอเขียนคำตอบ::The student uses a pencil to write the answer.
จ่าย|pay|verb|ฉันจ่ายเงินที่ร้าน::I pay money at the shop.|ลูกค้าจ่ายค่าน้ำชา::The customer pays for the tea.|พ่อจ่ายค่าตั๋วรถไฟ::Father pays for the train ticket.
เปลี่ยน|change|verb|ฉันเปลี่ยนเสื้อหลังฝนตก::I change my shirt after the rain.|ร้านเปลี่ยนราคาใหม่::The shop changes the price.|ครูเปลี่ยนเวลาเรียน::The teacher changes the class time.
เลือก|choose|verb|เด็กเลือกขนมหนึ่งชิ้น::The child chooses one snack.|ฉันเลือกเสื้อสีขาว::I choose a white shirt.|แม่เลือกผักสดที่ตลาด::Mother chooses fresh vegetables at the market.
สั่ง|order command|verb|เขาสั่งก๋วยเตี๋ยวที่ร้าน::He orders noodles at the shop.|แม่สั่งชาเย็นหนึ่งแก้ว::Mother orders one iced tea.|ลูกค้าสั่งอาหารจากเมนู::The customer orders food from the menu.
จอง|reserve book|verb|ฉันจองห้องโรงแรม::I book a hotel room.|พ่อจองตั๋วรถไฟพรุ่งนี้::Father books train tickets for tomorrow.|เราจองโต๊ะที่ร้านอาหาร::We reserve a table at the restaurant.
เดินทาง|travel|verb noun|เราเดินทางไปทะเลวันเสาร์::We travel to the sea on Saturday.|พ่อเดินทางด้วยรถไฟ::Father travels by train.|การเดินทางครั้งนี้สนุก::This trip is fun.
ขับ|drive|verb|พ่อขับรถไปทำงาน::Father drives to work.|คนขับขับรถเมล์ช้าๆ::The driver drives the bus slowly.|เธอขับรถได้ดี::She drives well.
ขี่|ride|verb|เด็กขี่จักรยานในสวน::The child rides a bicycle in the park.|พี่ขี่ม้าในสนาม::My older sibling rides a horse in the field.|ฉันขี่จักรยานไปตลาด::I ride a bicycle to the market.
บิน|fly|verb|นกบินบนฟ้า::The bird flies in the sky.|เครื่องบินบินไปกรุงเทพ::The airplane flies to Bangkok.|เด็กวาดนกที่กำลังบิน::The child draws a bird that is flying.
ว่ายน้ำ|swim|verb|เด็กว่ายน้ำในสระ::The child swims in the pool.|ฉันชอบว่ายน้ำที่ทะเล::I like swimming in the sea.|พี่สอนน้องว่ายน้ำ::The older sibling teaches the younger sibling to swim.
ยืน|stand|verb|ฉันยืนหน้าประตู::I stand in front of the door.|เด็กยืนรอรถเมล์::The child stands waiting for the bus.|ครูยืนข้างกระดาน::The teacher stands beside the board.
พัก|rest stay|verb|ฉันพักหลังทำงาน::I rest after working.|เราพักที่โรงแรมสองคืน::We stay at the hotel for two nights.|เด็กพักใต้ต้นไม้::The child rests under the tree.
เริ่ม|start begin|verb|บทเรียนเริ่มเก้าโมง::The lesson starts at nine.|ฉันเริ่มอ่านหนังสือใหม่::I start reading a new book.|ฝนเริ่มตกตอนเย็น::It starts to rain in the evening.
จบ|finish end|verb|ชั้นเรียนจบตอนบ่าย::The class ends in the afternoon.|ฉันทำการบ้านจบแล้ว::I finished the homework.|ภาพยนตร์จบเร็ว::The movie ends early.
รู้|know|verb|ฉันรู้ทางไปตลาด::I know the way to the market.|ครูรู้ชื่อของนักเรียน::The teacher knows the student's name.|เด็กรู้คำตอบแล้ว::The child knows the answer now.
เข้าใจ|understand|verb|ฉันเข้าใจบทเรียนนี้::I understand this lesson.|ครูพูดช้าเพื่อให้เราเข้าใจ::The teacher speaks slowly so we understand.|เด็กเข้าใจคำถามง่ายๆ::The child understands the easy question.
จำ|remember|verb|ฉันจำชื่อครูได้::I remember the teacher's name.|เด็กจำทางกลับบ้าน::The child remembers the way home.|เขาจำคำตอบเก่าไม่ได้::He cannot remember the old answer.
ลืม|forget|verb|ฉันลืมกุญแจที่บ้าน::I forget the key at home.|เด็กลืมสมุดที่โรงเรียน::The child forgets the notebook at school.|อย่าลืมปิดไฟ::Do not forget to turn off the light.
คิด|think|verb|ฉันคิดว่าชานี้อร่อย::I think this tea is delicious.|เด็กคิดคำตอบช้าๆ::The child thinks of the answer slowly.|แม่คิดเรื่องอาหารเย็น::Mother thinks about dinner.
พบ|meet find|verb|ฉันพบเพื่อนที่สถานี::I meet a friend at the station.|ครูพบหนังสือบนโต๊ะ::The teacher finds a book on the table.|เราพบกันวันจันทร์::We meet on Monday.
พา|take lead|verb|แม่พาลูกไปโรงเรียน::Mother takes the child to school.|พ่อพาเราไปทะเล::Father takes us to the sea.|ครูพานักเรียนไปห้องสมุด::The teacher takes students to the library.
ตาม|follow according to|verb preposition|เด็กตามแม่ไปตลาด::The child follows mother to the market.|ฉันทำตามคำสอนของครู::I follow the teacher's instruction.|เขาเดินตามทางไปสถานี::He walks along the way to the station.
ขอ|ask for request|verb|ขอน้ำหนึ่งแก้วครับ::One glass of water, please.|ฉันขอปากกาจากครู::I ask the teacher for a pen.|เด็กขอขนมจากแม่::The child asks mother for a snack.
ขอบใจ|thanks informal|polite phrase|ขอบใจนะเพื่อน::Thanks, friend.|พี่พูดขอบใจกับน้อง::The older sibling says thanks to the younger sibling.|ฉันขอบใจเธอที่ช่วย::I thank you for helping.
บอก|tell say|verb|แม่บอกให้เด็กนอนเร็ว::Mother tells the child to sleep early.|ครูบอกเวลาเรียนใหม่::The teacher tells the new class time.|ฉันบอกทางไปตลาด::I tell the way to the market.
เล่า|tell narrate|verb|ตาเล่าเรื่องเก่าให้เด็กฟัง::Grandfather tells an old story to the child.|ครูเล่าเรื่องสั้นในห้อง::The teacher tells a short story in the room.|แม่เล่าเรื่องตลาดให้ฉันฟัง::Mother tells me about the market.
แนะนำ|recommend introduce|verb|ครูแนะนำหนังสือง่ายๆ::The teacher recommends an easy book.|เพื่อนแนะนำร้านกาแฟใกล้สถานี::A friend recommends a coffee shop near the station.|แม่แนะนำให้ดื่มน้ำมากขึ้น::Mother suggests drinking more water.
รู้จัก|know be acquainted|verb|ฉันรู้จักครูคนนี้::I know this teacher.|เขารู้จักโรงแรมนี้::He knows this hotel.|เรารู้จักเพื่อนบ้านใหม่::We know the new neighbor.
พบกัน|meet each other|verb phrase|เราพบกันที่สถานี::We meet each other at the station.|เพื่อนพบกันวันเสาร์::Friends meet each other on Saturday.|ครูกับนักเรียนพบกันในห้องเรียน::The teacher and students meet in the classroom.
ลอง|try|verb|ฉันลองอ่านภาษาไทย::I try reading Thai.|เด็กลองกินมะม่วงเปรี้ยว::The child tries eating sour mango.|แม่ลองเสื้อใหม่ที่ร้าน::Mother tries a new shirt at the shop.
ฝึก|practice|verb|นักเรียนฝึกเขียนตัวเลข::The student practices writing numbers.|ฉันฝึกพูดภาษาไทยทุกวัน::I practice speaking Thai every day.|เด็กฝึกว่ายน้ำกับพี่::The child practices swimming with the older sibling.
ทวน|review|verb|ฉันทวนบทเรียนตอนเย็น::I review the lesson in the evening.|ครูทวนคำถามก่อนสอบ::The teacher reviews questions before the test.|นักเรียนทวนคำศัพท์ในสมุด::The student reviews vocabulary in the notebook.
แปล|translate|verb|ครูแปลประโยคเป็นภาษาอังกฤษ::The teacher translates the sentence into English.|ฉันแปลเมนูไม่หมด::I cannot translate the whole menu.|นักเรียนแปลคำตอบสั้นๆ::The student translates the short answer.
ห้องเรียน|classroom|noun|ห้องเรียนอยู่ชั้นสอง::The classroom is on the second floor.|นักเรียนนั่งในห้องเรียน::The students sit in the classroom.|ห้องเรียนนี้สว่างและสะอาด::This classroom is bright and clean.
ชั้น|floor class level|noun|สำนักงานอยู่ชั้นสาม::The office is on the third floor.|ฉันเรียนอยู่ชั้นนี้::I study in this class.|เขาขึ้นไปชั้นสอง::He goes up to the second floor.
บันได|stairs|noun|บันไดอยู่ข้างลิฟต์::The stairs are beside the elevator.|เด็กขึ้นบันไดช้าๆ::The child goes up the stairs slowly.|อย่าวิ่งบนบันได::Do not run on the stairs.
ลิฟต์|elevator|noun|ลิฟต์อยู่หน้าอาคาร::The elevator is in front of the building.|เราใช้ลิฟต์ขึ้นชั้นสาม::We use the elevator to go to the third floor.|ลิฟต์เปิดช้าในตอนเช้า::The elevator opens slowly in the morning.
ระเบียง|balcony|noun|ระเบียงห้องมีต้นไม้เล็ก::The room balcony has a small tree.|เสื้อแห้งอยู่บนระเบียง::The dry shirt is on the balcony.|ฉันยืนที่ระเบียงตอนเย็น::I stand on the balcony in the evening.
กำแพง|wall|noun|กำแพงสีขาวอยู่หลังบ้าน::The white wall is behind the house.|เด็กวาดรูปบนกระดาษไม่ใช่กำแพง::The child draws on paper, not the wall.|หน้ากำแพงมีดอกไม้::There are flowers in front of the wall.
หลังคา|roof|noun|หลังคาบ้านสีแดง::The house roof is red.|ฝนตกบนหลังคาเสียงดัง::Rain falls loudly on the roof.|พ่อดูหลังคาหลังฝนตก::Father looks at the roof after the rain.
พื้น|floor ground|noun|พื้นห้องสะอาดมาก::The room floor is very clean.|เด็กนั่งบนพื้นในสวน::The child sits on the ground in the park.|แม่เช็ดพื้นครัวตอนเช้า::Mother wipes the kitchen floor in the morning.
เพดาน|ceiling|noun|เพดานห้องสูงมาก::The room ceiling is very high.|ไฟอยู่บนเพดาน::The light is on the ceiling.|เด็กมองเพดานก่อนนอน::The child looks at the ceiling before sleeping.
สบู่|soap|noun|สบู่อยู่ในห้องน้ำ::The soap is in the bathroom.|ฉันล้างมือด้วยสบู่::I wash my hands with soap.|แม่ซื้อสบู่ที่ร้าน::Mother buys soap at the shop.
แชมพู|shampoo|noun|แชมพูอยู่ข้างสบู่::The shampoo is beside the soap.|ฉันใช้แชมพูตอนอาบน้ำ::I use shampoo when bathing.|ร้านขายแชมพูและสบู่::The shop sells shampoo and soap.
ผ้าเช็ดตัว|towel|noun|ผ้าเช็ดตัวแขวนในห้องน้ำ::The towel hangs in the bathroom.|ฉันใช้ผ้าเช็ดตัวหลังอาบน้ำ::I use a towel after bathing.|ผ้าเช็ดตัวเปียกอยู่บนระเบียง::The wet towel is on the balcony.
ยา|medicine|noun|ยาอยู่ในตู้เล็ก::The medicine is in the small cabinet.|หมอให้ยาแก่แม่::The doctor gives medicine to mother.|ยานี้ขมแต่ช่วยได้::This medicine is bitter but helps.
ร้านยา|pharmacy|noun|ร้านยาอยู่ใกล้โรงพยาบาล::The pharmacy is near the hospital.|แม่ซื้อยาที่ร้านยา::Mother buys medicine at the pharmacy.|ร้านยาเปิดตอนเช้า::The pharmacy opens in the morning.
แปรงสีฟัน|toothbrush|noun|แปรงสีฟันอยู่ในแก้ว::The toothbrush is in the cup.|ฉันใช้แปรงสีฟันทุกเช้า::I use a toothbrush every morning.|แม่ซื้อแปรงสีฟันใหม่ให้เด็ก::Mother buys a new toothbrush for the child.
ยาสีฟัน|toothpaste|noun|ยาสีฟันอยู่ข้างแปรงสีฟัน::The toothpaste is beside the toothbrush.|เด็กใช้ยาสีฟันนิดหน่อย::The child uses a little toothpaste.|แม่ซื้อยาสีฟันที่ร้านยา::Mother buys toothpaste at the pharmacy.
กระจก|mirror glass|noun|กระจกอยู่ในห้องน้ำ::The mirror is in the bathroom.|ฉันมองกระจกตอนเช้า::I look in the mirror in the morning.|กระจกหน้าต่างสะอาดมาก::The window glass is very clean.
อ่างล้างหน้า|sink|noun|อ่างล้างหน้าอยู่ใต้กระจก::The sink is under the mirror.|เด็กล้างมือที่อ่างล้างหน้า::The child washes hands at the sink.|แม่เช็ดอ่างล้างหน้าให้สะอาด::Mother wipes the sink clean.
ผ้า|cloth fabric|noun|ผ้าสีขาวอยู่บนโต๊ะ::The white cloth is on the table.|แม่เช็ดมือด้วยผ้า::Mother wipes her hands with a cloth.|ร้านนี้ขายผ้าสวย::This shop sells beautiful fabric.
ผ้าห่ม|blanket|noun|ผ้าห่มอยู่บนเตียง::The blanket is on the bed.|น้องใช้ผ้าห่มตอนหนาว::My younger sibling uses a blanket when cold.|แม่ซักผ้าห่มวันเสาร์::Mother washes the blanket on Saturday.
หมอน|pillow|noun|หมอนอยู่บนเตียงเล็ก::The pillow is on the small bed.|เด็กกอดหมอนก่อนนอน::The child hugs the pillow before sleeping.|หมอนใบนี้นุ่มมาก::This pillow is very soft.
โซฟา|sofa|noun|โซฟาอยู่ในห้องนั่งเล่น::The sofa is in the living room.|พ่อนั่งบนโซฟาอ่านข่าว::Father sits on the sofa and reads the news.|แมวนอนบนโซฟา::The cat sleeps on the sofa.
ทีวี|TV|noun|ทีวีอยู่หน้าโซฟา::The TV is in front of the sofa.|เด็กดูทีวีกับพ่อ::The child watches TV with father.|แม่ปิดทีวีก่อนนอน::Mother turns off the TV before sleeping.
วิทยุ|radio|noun|วิทยุอยู่บนตู้::The radio is on the cabinet.|พ่อฟังข่าวจากวิทยุ::Father listens to news from the radio.|วิทยุเสียงดังตอนเช้า::The radio is loud in the morning.
อินเทอร์เน็ต|internet|noun|อินเทอร์เน็ตที่บ้านเร็ว::The internet at home is fast.|ฉันใช้อินเทอร์เน็ตดูแผนที่::I use the internet to look at a map.|โรงแรมมีอินเทอร์เน็ตฟรี::The hotel has free internet.
คอมพิวเตอร์|computer|noun|คอมพิวเตอร์อยู่ในสำนักงาน::The computer is in the office.|นักเรียนใช้คอมพิวเตอร์เขียนงาน::The student uses a computer to write work.|พ่อซื้อคอมพิวเตอร์ใหม่::Father buys a new computer.
กล้อง|camera|noun|กล้องอยู่ในกระเป๋า::The camera is in the bag.|ฉันใช้กล้องถ่ายรูปทะเล::I use a camera to take a photo of the sea.|พ่อวางกล้องบนโต๊ะ::Father puts the camera on the table.
เสียง|sound voice|noun|เสียงนกร้องตอนเช้า::The sound of birds comes in the morning.|เสียงรถดังบนถนน::The car sound is loud on the road.|ครูใช้เสียงเบาในห้องสมุด::The teacher uses a soft voice in the library.
กลิ่น|smell|noun|กลิ่นกาแฟหอมมาก::The smell of coffee is very nice.|ในครัวมีกลิ่นอาหาร::There is a food smell in the kitchen.|เด็กไม่ชอบกลิ่นยา::The child does not like the smell of medicine.
รอยยิ้ม|smile|noun|รอยยิ้มของแม่สวย::Mother's smile is beautiful.|เด็กมีรอยยิ้มบนใบหน้า::The child has a smile on the face.|รอยยิ้มทำให้ห้องสดใส::A smile makes the room bright.
ของขวัญ|gift|noun|ของขวัญอยู่ในกล่อง::The gift is in the box.|แม่ให้ของขวัญวันเกิด::Mother gives a birthday gift.|เด็กเปิดของขวัญด้วยความดีใจ::The child opens the gift happily.
วันเกิด|birthday|noun|วันเกิดของน้องคือวันเสาร์::My younger sibling's birthday is Saturday.|เรากินขนมในวันเกิด::We eat snacks on the birthday.|แม่ซื้อของขวัญวันเกิด::Mother buys a birthday gift.
งานเลี้ยง|party|noun|งานเลี้ยงเริ่มตอนเย็น::The party starts in the evening.|ครอบครัวไปงานเลี้ยงวันเกิด::The family goes to a birthday party.|ในงานเลี้ยงมีอาหารมาก::There is a lot of food at the party.
กีฬา|sports|noun|กีฬาทำให้ร่างกายแข็งแรง::Sports make the body strong.|เด็กชอบกีฬาในโรงเรียน::The child likes sports at school.|วันเสาร์เราดูกีฬา::On Saturday we watch sports.
ฟุตบอล|football soccer|noun|ฟุตบอลอยู่ในสนาม::Football is on the field.|พ่อดูฟุตบอลกับเพื่อน::Father watches football with friends.|เด็กเล่นฟุตบอลหลังเลิกเรียน::The child plays football after school.
เกม|game|noun|เกมนี้สนุกมาก::This game is very fun.|เด็กเล่นเกมกับพี่::The child plays a game with the older sibling.|เราเล่นเกมหลังทำการบ้าน::We play a game after doing homework.
ภาพยนตร์|movie|noun|ภาพยนตร์เริ่มสองทุ่ม::The movie starts at eight at night.|ฉันดูภาพยนตร์กับเพื่อน::I watch a movie with a friend.|ภาพยนตร์เรื่องนี้ไม่น่าเบื่อ::This movie is not boring.
ละคร|drama play|noun|ละครวันนี้สนุก::Today's drama is fun.|แม่ดูละครตอนกลางคืน::Mother watches a drama at night.|นักเรียนเล่นละครสั้นในโรงเรียน::Students perform a short play at school.
เรื่อง|story matter|noun|เรื่องนี้สั้นและง่าย::This story is short and easy.|ตาเล่าเรื่องเก่าให้เด็กฟัง::Grandfather tells an old story to the child.|ฉันมีเรื่องจะถามครู::I have something to ask the teacher.
ตอน|part episode time|noun|ตอนเช้าอากาศเย็น::In the morning the weather is cool.|ละครตอนนี้สนุกมาก::This episode of the drama is very fun.|ตอนท้ายบทเรียนมีคำถาม::At the end of the lesson there are questions.
ครึ่ง|half|number noun|ฉันกินขนมปังครึ่งชิ้น::I eat half a piece of bread.|รถเมล์มาหกโมงครึ่ง::The bus comes at half past six.|เราเรียนครึ่งชั่วโมง::We study for half an hour.
ทั้งหมด|all whole|quantifier|นักเรียนทั้งหมดอยู่ในห้อง::All the students are in the room.|ฉันอ่านหนังสือทั้งหมดแล้ว::I read the whole book.|เงินทั้งหมดอยู่ในกระเป๋า::All the money is in the bag.
เอง|self by oneself|pronoun adverb|ฉันทำอาหารเองวันนี้::I make food by myself today.|เด็กอ่านหนังสือเองได้::The child can read by himself.|แม่บอกให้ฉันเลือกเอง::Mother tells me to choose by myself.
กัน|each other together|pronoun adverb|เรากินข้าวด้วยกัน::We eat together.|เด็กเล่นกันในสวน::The children play together in the park.|พรุ่งนี้เราพบกันที่สถานี::Tomorrow we meet each other at the station.
เลย|at all very|adverb|วันนี้ไม่ร้อนเลย::Today it is not hot at all.|อาหารอร่อยมากเลย::The food is really delicious.|ฉันไม่รู้ทางเลย::I do not know the way at all.
เท่านั้น|only|adverb|ฉันมีเงินสิบบาทเท่านั้น::I have only ten baht.|วันนี้เรามีเรียนหนึ่งชั่วโมงเท่านั้น::Today we have only one hour of class.|เขากินขนมปังเท่านั้น::He eats only bread.
บ่อย|often|adverb|ฉันไปตลาดบ่อย::I go to the market often.|เด็กอ่านหนังสือบ่อยขึ้น::The child reads books more often.|ฝนตกบ่อยในเดือนนี้::It rains often this month.
นาน|long time|adverb adjective|ฉันรอรถเมล์นาน::I wait for the bus for a long time.|เขาอยู่เมืองนี้นานแล้ว::He has lived in this city for a long time.|อย่านั่งนานเกินไป::Do not sit too long.
ทันที|immediately|adverb|แม่กลับบ้านทันทีหลังงาน::Mother returns home immediately after work.|เด็กดื่มน้ำทันทีเมื่อกระหาย::The child drinks water immediately when thirsty.|ฉันตอบอีเมลทันที::I answer the email immediately.
ประมาณ|about approximately|adverb|รถเมล์มาประมาณห้านาทีแล้ว::The bus came about five minutes ago.|บ้านอยู่ห่างตลาดประมาณหนึ่งกิโลเมตร::The house is about one kilometer from the market.|เราใช้เวลาประมาณครึ่งชั่วโมง::We use about half an hour.
จริง|true really|adjective adverb|คำตอบนี้จริงไหม::Is this answer true?|อาหารร้านนี้อร่อยจริง::The food at this shop is really delicious.|เขาพูดเรื่องจริงกับครู::He tells the true story to the teacher.
ปัญหา|problem|noun|ปัญหานี้ไม่ยาก::This problem is not difficult.|ครูช่วยนักเรียนแก้ปัญหา::The teacher helps the student solve the problem.|ถ้ามีปัญหาให้ถามฉัน::If there is a problem, ask me.
โอกาส|chance opportunity|noun|ฉันมีโอกาสเรียนภาษาไทย::I have a chance to study Thai.|เด็กได้โอกาสอ่านหนังสือใหม่::The child gets a chance to read a new book.|ขอบคุณสำหรับโอกาสนี้::Thank you for this opportunity.
ความสุข|happiness|noun|ครอบครัวคือความสุขของฉัน::Family is my happiness.|เด็กยิ้มด้วยความสุข::The child smiles with happiness.|วันเสาร์มีความสุขมาก::Saturday is very happy.
ความรัก|love|noun|ความรักของแม่อบอุ่น::A mother's love is warm.|เด็กได้รับความรักจากครอบครัว::The child receives love from the family.|เพลงนี้พูดถึงความรัก::This song talks about love.
สุขภาพ|health|noun|สุขภาพของพ่อดีขึ้น::Father's health is better.|อาหารดีช่วยสุขภาพ::Good food helps health.|หมอถามเรื่องสุขภาพของแม่::The doctor asks about mother's health.
โรงงาน|factory|noun|โรงงานอยู่ใกล้เมือง::The factory is near the city.|พ่อทำงานในโรงงาน::Father works in a factory.|รถเมล์ไปโรงงานตอนเช้า::The bus goes to the factory in the morning.
เกษตรกร|farmer|noun|เกษตรกรทำงานในสวน::The farmer works in the garden.|เกษตรกรขายผักที่ตลาด::The farmer sells vegetables at the market.|เด็กเห็นเกษตรกรใกล้หมู่บ้าน::The child sees a farmer near the village.
ชาวนา|rice farmer|noun|ชาวนาปลูกข้าวในนา::The rice farmer grows rice in the field.|ชาวนาตื่นเช้าเพื่อทำงาน::The farmer wakes early to work.|เราซื้อข้าวจากชาวนา::We buy rice from the rice farmer.
พยาบาล|nurse|noun|พยาบาลทำงานที่โรงพยาบาล::The nurse works at the hospital.|พยาบาลพูดกับเด็กอย่างอ่อนโยน::The nurse speaks gently with the child.|แม่ของฉันเป็นพยาบาล::My mother is a nurse.
ช่าง|technician craftsperson|noun|ช่างซ่อมจักรยานของพ่อ::The technician repairs father's bicycle.|ช่างมาที่บ้านตอนเช้า::The technician comes to the house in the morning.|เขาเป็นช่างในโรงงาน::He is a technician in the factory.
นักร้อง|singer|noun|นักร้องร้องเพลงบนเวที::The singer sings on the stage.|เด็กอยากเป็นนักร้อง::The child wants to be a singer.|นักร้องคนนี้เสียงดี::This singer has a good voice.
นักกีฬา|athlete|noun|นักกีฬาวิ่งเร็วมาก::The athlete runs very fast.|พี่ชายเป็นนักกีฬาที่โรงเรียน::My older brother is an athlete at school.|นักกีฬาดื่มน้ำหลังซ้อม::The athlete drinks water after practice.
นักท่องเที่ยว|tourist|noun|นักท่องเที่ยวดูแผนที่ในเมือง::The tourist looks at a map in the city.|โรงแรมมีนักท่องเที่ยวหลายคน::The hotel has many tourists.|นักท่องเที่ยวถามทางไปวัด::The tourist asks the way to the temple.
""".strip()


def parse_entries() -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    raw = "\n".join(part for part in [RAW, EXTRA_RAW] if part)
    for line_number, line in enumerate(raw.splitlines(), 1):
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
    if len(entries) != 500:
        raise ValueError(f"expected 500 entries, got {len(entries)}")
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


def build_batch(
    entries: list[dict[str, object]],
    start_index: int,
) -> list[dict[str, object]]:
    return [
        {
            "vocab_index": index,
            "word": entry["word"],
            "sentences": entry["sentences"],
        }
        for index, entry in enumerate(entries, start_index)
    ]


def build_explanations(
    entries: list[dict[str, object]],
    lexicon: dict[str, dict[str, str]],
) -> dict[str, list[dict[str, object]]]:
    rows = []
    current_id = ID_START
    for entry in entries:
        for sentence in entry["sentences"]:  # type: ignore[index]
            rows.append(
                {
                    "id": current_id,
                    "words": explain_thai_sentence(sentence["target"], lexicon, str(entry["word"])),
                }
            )
            current_id -= 1
    return {"data": rows}


def main() -> None:
    entries = parse_entries()
    write_json(CORPORA / "thai_a1_vocab.json", build_vocab(entries))
    lexicon = build_thai_lexicon(CORPORA / "thai_a1_vocab.json")
    for start in range(1, len(entries) + 1, 125):
        end = start + 124
        batch = entries[start - 1 : end]
        write_json(GENERATED / f"thai_{start:03d}_{end:03d}.json", build_batch(batch, start))
    write_json(CORPORA / "thai_a1_explanations.json", build_explanations(entries, lexicon))
    print(f"thai: wrote {len(entries)} words and {len(entries) * 3} explanations")


if __name__ == "__main__":
    main()
