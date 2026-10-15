#!/usr/bin/env python3
"""Write the IDS question master and the old-to-new crosswalk.

Internal working file. Does not change dealer results, Dealer Compare, or Forms.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_MD = ROOT / "00_docs" / "IDS_Question_Master.md"
OUT_CSV = ROOT / "00_docs" / "IDS_Question_Master_Crosswalk.csv"
HTML = ROOT / "02_dashboards" / "ids" / "IDS_2026_dealer_compare_Hungary.html"

# points: 2 questions x 8, 8 x 4, 4 x 2 = 56 per section. 5 x 56 = 280.
# Twelve questions at 4 plus two at 8 is 64, which would move the total off 280.


def Q(qid, section, points, text, partly, yes, old, na="", note=""):
    return {
        "id": qid,
        "section": section,
        "points": points,
        "text": text,
        "partly": partly,
        "yes": yes,
        "na": na,
        "old": old,
        "note": note,
    }


NA_BRAND = "Not applicable only when the main brand at this site forbids the Isuzu mark. It is left out of the section total. It is not a full mark."
NA_EV = "Not applicable only when the distributor confirms that no electric Isuzu is sold in this market. A dealer may not choose this alone."
NA_PRODUCT = "Not applicable only when the distributor does not offer this product in the market. A dealer may not choose this alone."

QUESTIONS = [
    # A. Premises. 8,4,4,4,8,8,4,4,2,2,4,4,4,4 and hours/building/warranty/charger at 2.
    Q("A01", "A", 4,
      "Does the dealer show an Isuzu sign that can be seen from the road, and is that sign clean and in line with the Isuzu sign manual?",
      "The sign is there, but it is dirty, faded, hard to see from the road, or not in line with the sign manual.",
      "It can be seen from the road, and it is clean and in line with the sign manual.",
      ["A.1-1", "A.1-3"],
      NA_BRAND),
    Q("A02", "A", 2,
      "Does the dealer show the Isuzu mark inside the building, in line with the Isuzu sign manual?",
      "The mark is in the building, but it is not in line with the sign manual.",
      "The mark is in the building and in line with the sign manual.",
      ["A.1-5", "A.1-6"],
      NA_BRAND),
    Q("A03", "A", 4,
      "Does the dealer keep the building, fences, parking surface, paint, outside lights, and drainage in good order?",
      "The site can be used, but paint, lights, fences, or drainage are in poor order.",
      "Building, fences, parking surface, paint, outside lights, and drainage are in good order.",
      ["A.1-2"]),
    Q("A04", "A", 2,
      "Does the dealer show the opening hours at every customer entrance, so they can be read when the site is closed?",
      "Hours are shown, but not at every customer entrance, or they cannot be read from outside when the site is closed.",
      "Hours are shown at every customer entrance and can be read when the site is closed.",
      ["A.1-4"]),
    Q("A05", "A", 8,
      "Does the dealer give customers their own parking, marked and lit during working hours after dark, and a signed way to reception that does not go through the office?",
      "Customer parking exists, but it is not marked or lit, the way to reception is unclear, or the customer has to walk through the office to reach reception, the waiting area, or the customer toilet.",
      "Parking is separate from staff parking, marked, lit after dark during working hours, and signed. The customer reaches reception, the waiting area, and the customer toilet without entering the office.",
      ["A.1-7", "A.1-8", "A.1-11"],
      note="8-point question."),
    Q("A06", "A", 8,
      "Does the dealer keep a service reception the customer can see from the entrance, with a clear counter, a computer for the job, and a secure place for the customer's keys?",
      "Reception is easy to find, but the counter is cluttered, or the computer or the key storage is missing.",
      "Reception is visible from the entrance. The counter holds only what the customer visit needs. The computer has the software the distributor requires. Keys are stored securely.",
      ["A.1-9", "A.1-10", "A.1-20"],
      note="8-point question. Replaces A.1-10, which gave points for saying unrelated items were on the counter. A clear counter is now the pass."),
    Q("A07", "A", 4,
      "Does the dealer offer a customer waiting area that is signed, clean, and has a drink, something to read, or wifi?",
      "A waiting area exists, but it is unsigned, untidy, or has nothing for the customer to use.",
      "It exists, it is signed, it is clean, and it offers a drink, something to read, or wifi.",
      ["A.1-12", "A.1-13", "A.1-14", "A.1-15"]),
    Q("A08", "A", 4,
      "Does the dealer offer a customer toilet, separate from the staff toilet, that is signed and clean?",
      "A customer toilet exists, but it is shared with staff, unsigned, or not clean.",
      "It is separate from the staff toilet, signed, and clean.",
      ["A.1-16", "A.1-17", "A.1-18"]),
    Q("A09", "A", 2,
      "Does the dealer display the warranty terms for Isuzu parts and accessories where the customer at reception can read them?",
      "A notice exists, but it is out of date or not where the customer stands.",
      "Current warranty terms for parts and accessories are on display at reception.",
      ["A.1-19"]),
    Q("A10", "A", 2,
      "Does the dealer provide a charger for electric vehicles in the parking area or the sales area?",
      "A charger is on site but customers cannot use it.",
      "A charger or wallbox is available in the parking area or the sales area.",
      ["A.1-21"],
      NA_EV),
    Q("A11", "A", 4,
      "Does the dealer use the Isuzu mark, in line with the Isuzu sign manual, on letterhead, on business cards, on the website, and on site vehicles?",
      "The mark is used on some of these, or it is used but not in line with the sign manual.",
      "Letterhead, business cards, the website, and site vehicles such as the service van and the parts van all carry the mark in line with the sign manual.",
      ["A.2-1", "A.2-2", "E.2-2", "E.2-3"],
      NA_BRAND,
      note="Website mark and vehicle livery move here from Vehicle sales so the mark is asked once."),
    Q("A12", "A", 4,
      "Does the dealer show current aftersales offers where the service customer can see them?",
      "Some offers or posters are out, but they are out of date or not in the service reception.",
      "Current offers, such as service contracts and vehicle health reports, are on display in the service reception. Other literature sits in the area it belongs to.",
      ["A.2-3", "A.2-4"]),
    Q("A13", "A", 4,
      "Does reception staff wear the service uniform, and does each person have a name badge or a name plate on the counter?",
      "Some people on reception are missing the uniform or a visible name.",
      "Everyone on reception wears the uniform and has a visible name.",
      ["A.3-1", "A.3-2"],
      NA_BRAND),
    Q("A14", "A", 4,
      "Do technicians wear safety shoes, and is their clothing Isuzu or plain, at least as visible as any other brand?",
      "Safety shoes are worn, but other-brand clothing is more visible than Isuzu or plain clothing.",
      "Safety shoes are worn, and technician clothing is Isuzu or plain, at least as visible as any other brand.",
      ["A.3-3", "A.3-4"],
      note="No Not applicable. Safety shoes stay in the score even when the main brand forbids an Isuzu uniform. If Isuzu clothing is forbidden, Partly is the right mark when the shoes are worn."),

    # B. Organisation
    Q("B01", "B", 8,
      "Does the dealer have a written Isuzu plan for the year, with a service target and a parts target, based on the Isuzu vehicles in its area?",
      "A plan exists, but it has no service target, or no parts target, or it ignores the local vehicle park.",
      "The plan is written, it is updated for the workshop and for the distributor's marketing plan, it has both targets, and the dealer knows how many Isuzu vehicles are in its area.",
      ["B.1-1", "B.1-2", "B.1-3", "B.1-4", "B.1-5"],
      note="8-point question."),
    Q("B02", "B", 8,
      "Does the dealer have at least one technician trained on Isuzu?",
      "One technician has Isuzu training.",
      "On every shift there is at least one Isuzu master technician and one person trained on Isuzu parts.",
      ["B.2-6", "B.3-6"],
      note="8-point question."),
    Q("B03", "B", 4,
      "Does the dealer principal review the plan with the distributor, and does the dealer repeat this standards check on a set cycle?",
      "The review happens, or the standards check is repeated, but not both.",
      "The principal is available for reviews with reasonable notice, and the dealer repeats this standards check on a cycle the distributor sets.",
      ["B.1-6", "B.7-1"]),
    Q("B04", "B", 2,
      "Does the dealer keep an organisation chart, updated this year, that shows who is responsible, including a principal or general manager?",
      "A chart exists, but it is old, roles are unclear, or no principal is named.",
      "The chart shows the date of this year's update, roles are clear, a principal or general manager is named, and the customer can see who is responsible.",
      ["B.2-1", "B.2-2", "B.2-3", "B.2-4", "B.2-10"]),
    Q("B05", "B", 4,
      "Does the dealer name a service advisor for Isuzu, a person for parts, a person for warranty and maintenance plans, and cover for service and parts management?",
      "Some of these roles are filled.",
      "A service advisor, a parts person, and a warranty administrator are named. Service management and parts management are named where the site has those jobs.",
      ["B.2-5", "B.2-7", "B.2-9", "B.2-11"]),
    Q("B06", "B", 4,
      "Does the dealer review each person's skills, keep a training plan, and track the quality of technicians' work?",
      "Skills are reviewed, or a training plan exists, but not both.",
      "Skills are reviewed on a regular cycle, each person has a training plan, and technician work quality is tracked.",
      ["B.2-8", "B.3-1", "B.3-2"]),
    Q("B07", "B", 4,
      "Does the person responsible for training attend Isuzu or distributor training, and then train the relevant people in the dealership?",
      "Someone attends, but the workshop is not trained afterwards.",
      "The person attends, and runs an internal session for the relevant people soon afterwards.",
      ["B.3-3", "B.3-4"]),
    Q("B08", "B", 2,
      "Does the dealer have trained cover for key roles during sickness and holiday, and a named successor for those roles?",
      "Cover exists, or a successor is named, but not both.",
      "Trained cover exists for sickness and holiday, and a successor is named.",
      ["B.3-5"]),
    Q("B09", "B", 4,
      "Does the dealer meet local law on fire equipment and fire signs, hazardous goods, waste, worker safety, and a marked bay for disabled customers?",
      "Most of these are in place, but one legal item is missing.",
      "Fire equipment and signs, hazardous-goods control, waste disposal, worker safety, and a marked disabled bay all meet local law. Nothing is stored in front of fire equipment.",
      ["B.4-1", "B.4-2", "B.4-3", "B.4-4", "B.4-5", "B.4-6"],
      note="Fire, waste, and the disabled bay stay. They are one legal check, not six taps."),
    Q("B10", "B", 4,
      "Does the dealer hold the certificates required to handle and service electric vehicles, for every person who does that work?",
      "Some of the people who work on high voltage are certified, not all who need to be.",
      "Every person who handles or services electric vehicles holds the required certificate.",
      ["B.4-7"],
      NA_EV),
    Q("B11", "B", 2,
      "Does the dealer hold insurance that covers the ordinary running of the dealership, including vehicles left in its care?",
      "Insurance exists, but workshop risk, vehicles in care, or public liability is clearly missing.",
      "Cover is in place for ordinary operations, including vehicles left in the dealer's care.",
      ["B.4-8"]),
    Q("B12", "B", 4,
      "Does the dealer run a 5S check in the workshop and correct what the check finds?",
      "The workshop is mostly tidy, but a written check is missing, or findings are not acted on.",
      "Aisles are clear, tools are stored and labelled, floors are clean, staff washrooms are clean, documents have a place, a first-aid kit is in the workshop, lifts and pits are inspected, a defibrillator is on site, and the 5S sheet is followed up.",
      ["B.5-1", "B.5-2", "B.5-3", "B.5-4", "B.5-5", "B.5-6", "B.5-7", "B.5-8", "B.5-9", "B.5-10", "B.5-11"]),
    Q("B13", "B", 4,
      "Does the dealer keep a customer and vehicle file, with contact details, VIN, registration, mileage and service history, and a privacy consent?",
      "Name, contact, and VIN are stored, but mileage, service history, or the privacy consent is missing.",
      "Name, address, phone, contact person, payment class, customer class, whether the customer has their own workshop, VIN, registration, mileage at each visit, and service history are on file. A privacy consent is checked and obtained when it is missing.",
      ["B.6-2", "B.6-3", "B.6-4", "B.6-5", "B.6-6", "B.6-7", "B.6-8", "B.6-9", "B.6-10"]),
    Q("B14", "B", 2,
      "Does the dealer run a regular satisfaction check after service, or take part in the distributor's satisfaction programme?",
      "Checks happen sometimes, or only part of the distributor's programme is used.",
      "Checks run on a regular cycle, or the dealer takes part in the whole distributor programme.",
      ["B.6-1"]),

    # C. Service
    Q("C01", "C", 8,
      "Does the dealer have the Isuzu diagnostic tool the distributor specifies, with the current software?",
      "The tool is on site, but the software is not current.",
      "The specified tool is on site and the software is current. Score the tool this distributor still uses. Do not mark a dealer down for a tool the distributor has withdrawn.",
      ["C.1-11", "C.1-12"],
      note="8-point question."),
    Q("C02", "C", 8,
      "Does the dealer get the customer's approval of the work, the price, and the time before any extra work starts?",
      "The customer is told, but work starts before approval, or the price or the new time is not agreed.",
      "Content, price, and delivery time are agreed before the extra work starts.",
      ["C.4-6", "C.4-9"],
      note="8-point question. C.4-6 also mentions a delay. The delay itself is scored under C13. This line is counted here so it is not scored twice."),
    Q("C03", "C", 4,
      "Does the workshop have light, ventilation, and a lift or pit that can take the heaviest and longest vehicle the dealer sells, plus jacks, a bench, a component area, and air-conditioning recovery?",
      "Light, ventilation, and a suitable lift or pit are in place, and one of jacks, bench, component area, or air-conditioning recovery is missing.",
      "All of them are in place.",
      ["C.1-1", "C.1-2", "C.1-3", "C.1-4", "C.1-5", "C.1-6", "C.1-7"]),
    Q("C04", "C", 4,
      "Does the dealer hold the required special tools, calibrated torque wrenches with records, and the ordinary tools, covers, and trolleys each technician needs?",
      "Most tools are there, but calibration records, special tools, covers, or a tool trolley are missing.",
      "Special tools are complete, torque wrenches have calibration records, each technician has ordinary tools, each bay has the required covers, and tools sit in a mobile cabinet. For a truck dealer, the covers required are the seat cover, floor mat, and steering-wheel cover.",
      ["C.1-8", "C.1-9", "C.1-10", "C.1-13", "C.1-14", "C.1-15"]),
    Q("C05", "C", 2,
      "Does the dealer provide personal protection, insulated tools, and a battery lift for work on electric vehicles?",
      "One or two of the three are on site.",
      "Personal protection, insulated tools, and a battery lift are all on site.",
      ["C.1-16", "C.1-17", "C.1-18"],
      NA_EV),
    Q("C06", "C", 4,
      "Does the dealer offer roadside help around the clock, with a published number and an equipped service van, and collect or deliver the vehicle outside hours when the customer asks?",
      "A 24-hour number exists, or a van exists, but the dealer does not actually provide roadside help.",
      "A 24-hour number is published, breakdown help is provided, an equipped service van is available, and the dealer collects or delivers outside hours when the customer asks.",
      ["A.1-22", "C.1-19", "C.1-20", "C.4-18"],
      note="The logo on the van is scored under A11, not here."),
    Q("C07", "C", 2,
      "Does the dealer provide enough changing space, lockers, a staff toilet, and a staff rest room for the people employed?",
      "A toilet and a place to change exist, but they are too small for the headcount, or there is no rest room.",
      "Lockers and changing space match the headcount, the staff toilet and washroom are sufficient, and there is a staff rest room.",
      ["C.2-1", "C.2-2", "C.2-3"]),
    Q("C08", "C", 4,
      "Does the dealer keep current Isuzu service information, on paper or online, and use it?",
      "Some manuals are current, or access exists but it is not used.",
      "The current service policy manual, workshop manual, owner's manual, labour times, and campaign information are on hand or online and are the versions the distributor has issued.",
      ["C.3-1", "C.3-2"],
      note="C.3-2 also names the parts catalogue. The catalogue is scored under D08. This line is counted here so it is not scored twice."),
    Q("C09", "C", 4,
      "Does the dealer store replaced warranty parts as Isuzu requires, tag them, carry out recalls, and report a safety or product issue to the distributor?",
      "Parts are kept, but tags, the storage period, recall records, or the reporting route are incomplete.",
      "There is rack space by month, each part is tagged with repair order, VIN, date, mileage and the fault, recalls are done to the service manual, and the route for a safety or product issue is clear.",
      ["C.3-3", "C.3-9", "C.3-10", "C.3-11"]),
    Q("C10", "C", 2,
      "Does the dealer store new vehicles so they do not deteriorate, complete the pre-delivery inspection and keep the sheet, and explain the warranty at handover?",
      "Storage or the pre-delivery inspection happens, but the sheets are not kept, or the warranty is not explained at handover.",
      "Storage checks are recorded, the pre-delivery inspection is done just before handover and the sheet is kept, and the warranty is explained with the booklet or certificate.",
      ["C.3-4", "C.3-5", "C.3-6", "C.3-7", "C.3-8"]),
    Q("C11", "C", 4,
      "Does the dealer run appointments, call customers in for scheduled maintenance, still take an urgent repair without an appointment, and send job counts to the distributor?",
      "Appointments exist, but nobody is named to call customers in, urgent work is refused, or job counts are not sent.",
      "There is an appointment system, a named person calls customers in from the customer and service records, urgent jobs are accepted, and the count of jobs and maintenances goes to the distributor.",
      ["C.4-1", "C.4-2", "C.4-3", "C.4-17", "C.4-20"]),
    Q("C12", "C", 4,
      "Does the dealer check the vehicle, agree the estimate, the price and the collection time with the customer, and give the technician a job sheet before work starts?",
      "An estimate is given, but approval, the collection time, or the job sheet is missing.",
      "The vehicle is checked, the customer approves the work, the price and the collection time, and the technician has a job sheet before work starts.",
      ["C.4-4", "C.4-5", "C.4-7", "C.4-8"]),
    Q("C13", "C", 4,
      "Does the dealer watch the job, agree any delay, inspect the finished work, explain it, state the next service, and keep a written record with any fault codes and the time taken?",
      "The customer gets an explanation, but the inspection, the written report, or the time record is missing.",
      "Progress is watched. A delay is explained and agreed. The finished job is inspected against a check sheet. The result and the next service are explained. Labour time follows Isuzu times or the dealer's own set times and is recorded. The technician's report names the complaint, the parts, and any fault codes. Maintenance records are kept.",
      ["C.3-12", "C.4-10", "C.4-11", "C.4-12", "C.4-13", "C.4-14", "C.4-19", "C.4-21", "C.4-22"]),
    Q("C14", "C", 2,
      "Does the dealer contact the customer within a week after the service and write down what the customer says?",
      "Some customers are contacted, or the contact is not written down.",
      "Contact is made within a week and the result is written down.",
      ["C.4-15"]),

    # D. Parts
    Q("D01", "D", 8,
      "Are Isuzu genuine parts stored apart from other brands, labelled, used on Isuzu repairs, and shown at the parts counter?",
      "Genuine parts are stored apart from other brands, but they are not labelled, not used on the repair, or not shown at the counter.",
      "They are stored apart, labelled, and used for Isuzu maintenance and repair. Genuine parts and the BVP range, where the distributor sells it, are displayed at the counter.",
      ["D.1-7", "D.1-8", "C.4-16"],
      note="8-point question. C.4-16 moves here so genuine parts are asked once. BVP is the Isuzu second range already named on the old sheet."),
    Q("D02", "D", 8,
      "Does the dealer run parts stock and orders in a system, and review stock and sales against a target every month?",
      "A system holds locations and orders, but monthly targets, a regular order of fast-moving parts, or an electronic stock file are missing.",
      "Locations support receiving and issuing. Recommended parts are flagged. Orders are calculated from demand. Fast-moving parts are ordered on a cycle. Stock value, fill, stock turn, and sales are checked against target every month. The dealer can produce a full electronic stock file.",
      ["D.1-3", "D.1-5", "D.1-6", "D.2-6", "D.2-7", "D.2-8", "D.2-9", "D.2-10", "D.2-17"],
      note="8-point question."),
    Q("D03", "D", 4,
      "Does the dealer have enough parts space for the stock it must hold and the stock it expects to sell?",
      "Space is tight for either the required stock or the expected stock.",
      "Space covers both the required stock and the stock expected from customer demand.",
      ["D.1-1", "D.1-11"]),
    Q("D04", "D", 4,
      "Is the parts store laid out for the way parts move, with a retail counter, a workshop counter, and a receiving area?",
      "The store works, but one counter is missing, or received goods have no place to wait.",
      "Layout follows how often parts move. There is a counter for retail and a counter for the workshop. Received goods have a place inside the store before they are put away.",
      ["D.1-2", "D.1-4", "D.1-12"]),
    Q("D05", "D", 4,
      "Can the dealer take parts deliveries during opening hours, and is there a covered, secure place for a delivery outside those hours?",
      "Deliveries are accepted in opening hours, but there is no secure place outside those hours.",
      "Both are in place.",
      ["D.1-9", "D.1-10"]),
    Q("D06", "D", 2,
      "Does the dealer keep oils, lubricants, and batteries in an area that meets local safety rules?",
      "An area exists, but it does not meet the local rule.",
      "The area meets local health and safety rules.",
      ["D.1-13"]),
    Q("D07", "D", 4,
      "Is the parts store tidy: clear doors, only parts inside, nothing left on the floor, and parts put away with the label facing out?",
      "Doors are clear and only parts are stored, but floors, labels, or put-away are poor.",
      "Doors are clear. Only parts are in the store. Nothing is left on floors or in aisles. Goods are sorted and put away when they arrive. Labels face out. Nothing is stored between bins. Heavy or large items are not stored on an upper shelf.",
      ["D.1-14", "D.1-15", "D.1-16", "D.1-17", "D.1-18", "D.1-19", "D.1-20", "D.1-21"]),
    Q("D08", "D", 4,
      "Does the dealer use the current Isuzu parts catalogue, on paper or online, and the same job documents as the workshop?",
      "A catalogue is available but it is not current, or the workshop uses a different document.",
      "The current catalogue and the parts manual are in use, on paper or online, and the workshop uses the same document format.",
      ["D.2-1", "D.2-2", "D.2-14"]),
    Q("D09", "D", 4,
      "When the workshop sends a parts request, does the dealer check stock and order what is missing?",
      "Stock is checked, but missing parts are not ordered straight away.",
      "Stock is checked and missing parts are ordered.",
      ["D.2-3"]),
    Q("D10", "D", 4,
      "Does the dealer name who orders, stores, and issues parts, and does that person attend the distributor's parts training?",
      "A person is named, but they do not attend the training, or the steps are unclear.",
      "The person and the steps for ordering, stocking, issuing, and stock control are clear, and that person attends the distributor's parts training.",
      ["D.2-4", "D.2-5"]),
    Q("D11", "D", 2,
      "Does the dealer split parts sales by product and by type of customer, and review those figures?",
      "One of the two splits is kept.",
      "Product groups and customer types are both reviewed. Product groups include parts, accessories, oil, tyres, batteries, and other. Customer types include the workshop, the counter, fleet, and trade.",
      ["D.2-11", "D.2-12"]),
    Q("D12", "D", 2,
      "Does the dealer record lost sales, split between price and supply?",
      "Some lost sales are noted, with no split between price and supply.",
      "Lost sales are recorded, split between price and back order.",
      ["D.2-15"]),
    Q("D13", "D", 4,
      "Does the dealer offer a maintenance plan or an extended warranty on parts?",
      "One of the two is offered.",
      "Both are offered where the distributor makes them available, and the offer is named on the visit record.",
      ["D.2-16"],
      NA_PRODUCT),
    Q("D14", "D", 2,
      "Do the parts and accessories the dealer sells meet local rules?",
      "The main lines do, and a known exception is still on sale.",
      "The parts and accessories sold meet local rules.",
      ["D.2-13"]),

    # E. Vehicle sales
    Q("E01", "E", 4,
      "Does the dealer name a person whose job is vehicle sales?",
      "Vehicle sales is covered, but nobody is named for it.",
      "A person is named for vehicle sales.",
      ["E.1-1"]),
    Q("E02", "E", 8,
      "Does the dealer run one Isuzu demonstrator at each sales site, on the latest specification, first registered within the last twelve months?",
      "A demonstrator is in use, but it is older than twelve months from first registration, or it is not the latest specification.",
      "One demonstrator per sales site, latest specification, first registered within the last twelve months. The body type is the dealer's choice.",
      ["E.1-2"],
      note="8-point question."),
    Q("E03", "E", 4,
      "Are the newest Isuzu models on display in the showroom?",
      "Models are on display, but they are not the current range.",
      "The newest models are on display.",
      ["E.1-3"]),
    Q("E04", "E", 4,
      "Are point-of-sale materials, pictures, posters, brochures, and specification sheets current and on display in customer areas?",
      "Materials are on display, but some are out of date or missing from a customer area.",
      "They are current and on display in the customer areas.",
      ["E.1-4"]),
    Q("E05", "E", 4,
      "Does the dealer track how fast sales leads are answered, follow them up, keep the customer record up to date, and track how many leads become sales?",
      "Leads are followed up, but response time or the conversion rate is not tracked.",
      "Response time, follow-up, the customer record, and the conversion rate are all kept.",
      ["E.1-5", "E.1-6", "E.1-7"]),
    Q("E06", "E", 4,
      "Does the dealer train the sales team on the features and benefits of the vehicles?",
      "Training happens, but not for the whole sales team, or not on the current models.",
      "Regular training covers the features and benefits of the current models for the sales team.",
      ["E.1-8"]),
    Q("E07", "E", 2,
      "Does the dealer use a system to manage vehicle sales?",
      "Sales are tracked, but not in a system.",
      "A system is used to manage vehicle sales.",
      ["E.1-9"]),
    Q("E08", "E", 4,
      "After delivery, does the dealer contact the customer to check they are satisfied and to ask what else they need?",
      "Some customers are contacted, or the contact does not ask what else they need.",
      "There is a set follow-up after every sale, covering satisfaction and any further need.",
      ["E.1-10"]),
    Q("E09", "E", 4,
      "When the vehicle is sold, does the dealer explain Isuzu servicing and suggest inspection and maintenance?",
      "Servicing is mentioned, without a clear suggestion of inspection and maintenance.",
      "The dealer explains the servicing standard and suggests inspection and maintenance.",
      ["E.1-11"]),
    Q("E10", "E", 8,
      "When the vehicle is sold, does the dealer offer a maintenance package or a warranty extension?",
      "The offer is mentioned, but it is not made as a set step of the sale.",
      "A maintenance package or a warranty extension is offered as a set step of the sale.",
      ["E.1-12"],
      NA_PRODUCT,
      note="8-point question."),
    Q("E11", "E", 4,
      "Does the dealer's website show current information for the models it sells?",
      "A website lists models, but the information is out of date.",
      "Current model information is on the website for the models sold.",
      ["E.2-1"]),
    Q("E12", "E", 2,
      "Does each department have its own email address, such as service and parts?",
      "One shared inbox covers every department.",
      "Service, parts, and sales each have their own address.",
      ["E.2-4"]),
    Q("E13", "E", 2,
      "Are the dealer's name, address, and opening hours correct on Google?",
      "A listing exists, but the name, address, or hours are wrong.",
      "Name, address, and opening hours are correct on Google.",
      ["E.2-5"]),
    Q("E14", "E", 2,
      "Does the dealer have its own website, and can a customer book a service appointment on it?",
      "The dealer has a website, but a service appointment cannot be booked on it.",
      "The dealer has its own website and a customer can book a service appointment on it.",
      ["E.2-6"]),
]

SECTIONS = {
    "A": "Premises, facility and clothing",
    "B": "Organisation and management",
    "C": "Service",
    "D": "Parts and accessories",
    "E": "Vehicle sales",
}


def _load_live_ids() -> set[str]:
    text = HTML.read_text(encoding="utf-8")
    i = text.find("const DATA = ")
    raw = text[i + len("const DATA = "):]
    depth = 0
    end = None
    for j, ch in enumerate(raw):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    data = json.loads(raw[:end])
    return {q["id"] for q in data["questions"]}


def validate() -> list[str]:
    errors: list[str] = []
    if len(QUESTIONS) != 70:
        errors.append(f"question count {len(QUESTIONS)} != 70")
    seen_new: set[str] = set()
    seen_old: list[str] = []
    for sec in "ABCDE":
        rows = [q for q in QUESTIONS if q["section"] == sec]
        if len(rows) != 14:
            errors.append(f"{sec} has {len(rows)} questions")
        pts = sum(q["points"] for q in rows)
        if pts != 56:
            errors.append(f"{sec} points {pts} != 56")
        eights = [q["id"] for q in rows if q["points"] == 8]
        fours = [q["id"] for q in rows if q["points"] == 4]
        twos = [q["id"] for q in rows if q["points"] == 2]
        if len(eights) != 2 or len(fours) != 8 or len(twos) != 4:
            errors.append(f"{sec} weights 8:{len(eights)} 4:{len(fours)} 2:{len(twos)}")
        for q in rows:
            if not q["text"].endswith("?"):
                errors.append(f"{q['id']} does not read as a question: {q['text'][:60]}")
            if q["id"] in seen_new:
                errors.append(f"duplicate new id {q['id']}")
            seen_new.add(q["id"])
            if q["points"] not in (2, 4, 8):
                errors.append(f"{q['id']} bad points {q['points']}")
            for old in q["old"]:
                seen_old.append(old)
    if len(seen_old) != len(set(seen_old)):
        dup = [x for x in seen_old if seen_old.count(x) > 1]
        errors.append(f"old ids repeated: {sorted(set(dup))}")
    live = _load_live_ids()
    got = set(seen_old)
    if got != live:
        errors.append(f"missing from master: {sorted(live - got)}")
        errors.append(f"not on live sheet: {sorted(got - live)}")
    if sum(q["points"] for q in QUESTIONS) != 280:
        errors.append("total points != 280")
    return errors


def _half(points: int) -> int:
    return points // 2


def render_md() -> str:
    lines: list[str] = []
    a = lines.append
    a("# IDS question master")
    a("")
    a("Internal until this wording is accepted. This is not a dealer file and it does not change this year's scores.")
    a("")
    a("The continental sheet has 196 questions and 280 points. The sections are not equal: Premises 46, Organisation 80, Service 80, Parts 47, Vehicle sales 27. This master keeps the five sections and the 280-point total, and it cuts the list to 70 questions by joining lines that ask the same thing.")
    a("")
    a("Twelve questions at 4 points plus two at 8 points is 64 points, not 56. That would move the total to 320 and break a like-for-like percentage. Each section is therefore two questions at 8, eight at 4, and four at 2. That is 56. Five sections are 280.")
    a("")
    a("UK trucks stay on their own list. They are not on this scale. UTI and UMI stay separate. A section that was not filled is not scored. It is not 0%.")
    a("")
    a("## How a question is scored")
    a("")
    a("Every question has the same answers: No, Partly, Yes. Some also have Not applicable.")
    a("")
    a("- No is 0.")
    a("- Partly is half the question, so 1, 2, or 4.")
    a("- Yes is the full 2, 4, or 8.")
    a("- Not applicable is left out of that dealer's section total. It is not a full mark and it is not a zero.")
    a("")
    a("The section result is points earned divided by points that applied. The dealer total is the same across the sections that were sat, not an average of the five percentages. A whole section with no answers is marked not scored and stays out of the total. That is the rule already used where premises, organisation, or vehicle sales were not filled.")
    a("")
    a("Not applicable is allowed only where this master says so: the main brand forbids the Isuzu mark, the distributor confirms that no electric Isuzu is sold in the market, or the distributor does not offer the maintenance plan or warranty extension. The dealer does not tick Not applicable on its own.")
    a("")
    a("The Isuzu sign manual means the brand rules for the Isuzu mark. On the old sheet those rules are named I.VIS and I.BIS. Those codes stay in the crosswalk. They are not in the question the auditor reads.")
    a("")
    a("## The 70 questions")
    a("")
    for sec in "ABCDE":
        rows = [q for q in QUESTIONS if q["section"] == sec]
        a(f"### {sec}. {SECTIONS[sec]} — 14 questions, 56 points")
        a("")
        for q in rows:
            a(f"**{q['id']} ({q['points']} points).** {q['text']}")
            a("")
            a(f"Old questions: {', '.join(q['old'])}.")
            a("")
            a(f"Partly: {q['partly']}")
            a("")
            a(f"Yes: {q['yes']}")
            a("")
            if q["na"]:
                a(q["na"])
                a("")
            if q["note"] and q["note"] != "8-point question.":
                a(f"Note: {q['note']}")
                a("")
    a("## Five Forms on the iPad")
    a("")
    a("One Form of 196 lines will not be finished on an iPad. Use the SharePoint site you already use for IDS. Add one page called Start a dealer visit, then five Forms, one per section.")
    a("")
    a("The page asks for country, dealer, date, and who is answering. Who is answering is either the dealer, in draft, or the distributor, confirming. Five buttons open the five Forms. Each Form is the 14 questions above, in order, plus one last question: photos of anything scored No. One upload for the section, not a photo on every line. The upload is shown every time. If a photo will not send, the Form can still be submitted. A No without a photo stays a No.")
    a("")
    a("Answers land in one SharePoint list. That list is the score. Nobody retypes a result workbook.")
    a("")
    a("Suggested columns on the answer list:")
    a("")
    a("- Country, dealer, visit date, person, role (draft or confirmed), status")
    a("- For each question: the answer, the points earned, and whether it was not applicable")
    a("- For each section: points earned, points that applied, percent, and a flag if the whole section was not scored")
    a("- Dealer total: points earned, points that applied, percent")
    a("- One photo link per section")
    a("")
    a("Do not trust the total that Forms shows on the iPad. Not applicable breaks a quiz total. Power Automate writes the official score: No is 0, Partly is half, Yes is full, and Not applicable is dropped from the points that applied. A confirmed row replaces that dealer's draft. Dealer Compare and the visit page read confirmed rows only.")
    a("")
    a("The dealer may fill the same five Forms before the visit. That row is a draft. Forms will not open the distributor's Form with the dealer's ticks already filled in. The distributor reads the draft on the SharePoint page and submits its own answers. Where the two differ, the distributor's answer stands. A sheet of Yes with nothing to show does not become the score.")
    a("")
    a("Dealer Compare stays the picture you send. It should read this list once the list exists. Until then, do not wait. The visit page below can be filled from this year's Dealer Compare by hand.")
    a("")
    a("## The visit")
    a("")
    a("Dealer Compare is how the distributor chooses who to visit. It is the wrong tool to walk around the workshop with. The visit agrees three actions. It does not create a new score.")
    a("")
    a("Before the day, open Dealer Compare and pick dealers below the country average. Start with the weakest.")
    a("")
    a("On site, if the Form is already confirmed, do not ask all 70 again. Confirm the two 8-point questions in each section, photograph what is No, and stop. If the Form is not in yet, fill it on the iPad during the visit. The distributor's answers are the ones that count.")
    a("")
    a("The visit page shows five lines, one per section: the question in that section with the most points left on the table. Points left are the question's full points minus the points earned. If two questions leave the same points, show the 8-point question. If a section was not scored, skip it. A dealer who sat only service and parts gets two lines, not five zeros.")
    a("")
    a("Under those lines, three empty actions. Three is the cap. The list should refuse a fourth open action for that dealer. A new action can be added when one closes, and there are still never more than three open.")
    a("")
    a("Each action names the dealer, the failed question in the words of this master, the owner at the dealer, the date, and the proof. Proof is a photo or a document back on the same list. Closed without proof stays open.")
    a("")
    a("Choose the three in this order. An 8-point question scored No. Then any other No on safety and waste (B09) or genuine parts (D01). Then the rest. Parts and Service come before a new outdoor sign when both are open.")
    a("")
    a("The next month is a filter on that list, not a new pack: dealers visited, actions still open, actions closed, dealers not yet visited. The score does not move because an action closed. The score moves at the next IDS only. The visit is not a forecast of parts sales.")
    a("")
    a("What you send the distributor is Dealer Compare, plus this visit page for the dealers they will walk. Do not build a separate study by hand for each country.")
    a("")
    a("### Visit page")
    a("")
    a("Dealer, country, visit date.")
    a("")
    a("Five lines, filled from the confirmed answers:")
    a("")
    a("- Premises: question, answer, points left")
    a("- Organisation: question, answer, points left")
    a("- Service: question, answer, points left")
    a("- Parts: question, answer, points left")
    a("- Vehicle sales: question, answer, points left")
    a("")
    a("Three actions, blank until the distributor writes them:")
    a("")
    a("- Action 1: question, what will be done, owner, date, proof")
    a("- Action 2: question, what will be done, owner, date, proof")
    a("- Action 3: question, what will be done, owner, date, proof")
    a("")
    a("Suggested columns on the action list: country, dealer, visit date, question id, question text, section, points left, action, owner, target date, proof link, status (open or closed), closed date.")
    a("")
    a("## What does not change")
    a("")
    a("France and Spain dealers already kept out of the average stay out of the average. UK trucks are not rescored onto this sheet. UTI is not added to UMI. A percentage quoted from this master is out of the points that applied, and the full scale is 280 only when all five sections were sat.")
    a("")
    a("The old question numbers sit on each line above. The same map is in the crosswalk file next to this one, one row per old question.")
    a("")
    a(f"Crosswalk: `{OUT_CSV}`")
    a("")
    return "\n".join(lines)


def write_csv() -> None:
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "old_id", "old_section", "new_id", "new_section", "new_points",
            "new_question", "note",
        ])
        for q in QUESTIONS:
            for old in q["old"]:
                w.writerow([
                    old, old.split(".")[0], q["id"], q["section"], q["points"],
                    q["text"], q["note"],
                ])


def main() -> None:
    errors = validate()
    if errors:
        raise SystemExit("\n".join(errors))
    OUT_MD.write_text(render_md(), encoding="utf-8")
    write_csv()
    n_old = sum(len(q["old"]) for q in QUESTIONS)
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_CSV}")
    print(f"questions={len(QUESTIONS)} old_ids={n_old} points={sum(q['points'] for q in QUESTIONS)}")


if __name__ == "__main__":
    main()
