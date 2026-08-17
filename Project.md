Project: Voice-Assisted Vehicle & Tire Registration

Objective

Automate and simplify the registration of vehicles and seasonal tire changes in the workshop.

Current workflow

Mechanic
   ↓
Fills out paper form by hand
   ↓
Office worker reads form
   ↓
Office worker manually types data into WERBAS

Main problem

The mechanic has to stop working and manually document information. The office worker then performs essentially the same data-entry work a second time.

The primary goal is therefore:

Reduce the mechanic’s documentation effort to a minimum while giving the office worker a clean, structured digital record for verification.

⸻

Core Concept

Build a voice-assisted workshop intake system.

The mechanic speaks naturally while working instead of filling out a form.

Example:

“Neueinlagerung. Kennzeichen CW-AB 123, Kilometerstand 82.450. Winterreifen 205 55 R16, Michelin Alpin 6, vorne 5 Millimeter, hinten 4 Millimeter, vier Stück, Zustand gut.”

The system converts this into structured information:

Customer:            New customer
License plate:       CW-AB 123
Mileage:             82,450 km
Tire type:           Winter
Tire size:           205/55 R16
Manufacturer:        Michelin
Model:               Alpin 6
Quantity:             4
Tread depth front:   5 mm
Tread depth rear:    4 mm
Condition:           Good

The mechanic then quickly confirms the result.

Mechanic
   ↓
Speaks naturally
   ↓
Speech recognition
   ↓
AI / data extraction
   ↓
Structured tire/vehicle record
   ↓
Mechanic confirms
   ↓
Office worker reviews
   ↓
WERBAS

⸻

Design Principles

1. Minimize mechanic interaction

The mechanic should not be expected to fill out another digital form.

The ideal interaction is:

Speak → Confirm → Continue working

The system should work while the mechanic is physically working on the vehicle.

⸻

2. Voice-first input

Voice recognition is the central input mechanism.

It should understand natural workshop language rather than forcing predefined phrases.

Examples:

“205 55 R16 Michelin, fünf Millimeter vorne, vier hinten.”

“Sommerreifen, Continental, 225 45 17, vorne sechs, hinten fünf.”

The system should normalize this into consistent structured data.

⸻

3. AI should extract structure, not invent information

Speech recognition may produce uncertainty.

Example:

“Michelin Alpin … irgendwas.”

The system should not guess the exact model.

Instead:

Tire model:
Michelin Alpin [uncertain]
⚠ Please verify

Uncertain fields should be explicitly flagged for human review.

⸻

Data Model

The initial system should produce structured records independently of WERBAS.

Vehicle

License plate
VIN (optional/future)
Make
Model
Mileage
Existing/new customer

Customer

For new customers, the mechanic should only provide the information necessary to identify the vehicle.

The office worker can later enter:

Name
Address
Phone
E-mail
Billing information
Customer number

The mechanic should not be burdened with administrative customer data.

Tire Set

Tire type
Tire size
Manufacturer
Model
Quantity
Tread depth front
Tread depth rear
Condition

Potential future fields:

DOT
Season
Rim type
Rim size
Storage location
Tire position
TPMS information

Service

Service performed
Additional notes
Date
Mechanic

⸻

Human Validation

The first version should not automatically write directly into WERBAS.

Instead:

Mechanic
   ↓
AI extraction
   ↓
Office review
   ↓
WERBAS

The office worker acts as a quality-control step.

Example review interface:

NEW VEHICLE REGISTRATION
CW-AB 123
82,450 km
WINTER TIRES
205/55 R16
Michelin Alpin 6
4 tires
Front tread: 5 mm
Rear tread: 4 mm
Condition: Good
[ Confirm ]   [ Edit ]

The office worker can correct individual fields rather than retyping the entire form.

⸻

Hybrid Input

Voice should be the primary input, but some repetitive categorical values can be represented by quick buttons.

Example:

Tire type:
[ SUMMER ] [ WINTER ] [ ALL-SEASON ]
Condition:
[ GOOD ] [ OK ] [ REPLACE ]
Quantity:
[ 4 ] [ 2 ] [ 1 ]

This creates a hybrid system:

Voice for descriptive information + buttons for repetitive categorical information.

⸻

Existing Customers

Existing customers are an important future optimization.

The license plate can be used to search the existing database.

Example:

CW-AB 123
      ↓
Vehicle found
      ↓
Max Mustermann
Audi A3
Last visit: ...

The mechanic does not need to re-enter information that already exists.

For a new customer:

License plate
   ↓
No match
   ↓
New vehicle/customer record
   ↓
Office worker completes customer details

⸻

License Plate Recognition

A future feature could allow the mechanic to point a phone/tablet camera at the plate.

Camera
   ↓
License plate recognition
   ↓
CW-AB 123

This removes another manual input step.

Possible future combination:

License plate → identifies vehicle/customer
VIN → verifies vehicle

⸻

Document / OCR Input

A future feature could allow photographs of vehicle documents such as registration papers.

OCR could extract:

License plate
VIN
Manufacturer
Vehicle type
First registration
Engine information

This should complement voice input rather than replace it.

⸻

Photos

Damage photos are not a priority for this project.

The project is primarily focused on:

* seasonal tire changes
* tire specifications
* vehicle registration
* reducing documentation effort

Photos may be considered later for documentation, but they are outside the initial scope.

⸻

WERBAS Integration

WERBAS integration is a future extension, not part of the initial MVP.

The architecture should therefore deliberately separate:

Input / AI
    ↓
Internal structured data model
    ↓
Human verification
    ↓
External system

This makes it possible to later connect:

* WERBAS REST/API
* database interfaces
* import interfaces
* other integrations

without redesigning the voice-registration system.

Potential final workflow:

Mechanic
   ↓
Voice
   ↓
AI extraction
   ↓
Office confirmation
   ↓
WERBAS API
   ↓
Repair / tire order

Eventually, depending on reliability, parts of the human step could potentially be automated further.

⸻

Proposed MVP

The first version should stay deliberately small.

MVP workflow

1. Mechanic starts a new registration
2. Mechanic speaks
3. Speech is transcribed
4. AI extracts structured tire/vehicle data
5. Missing or uncertain fields are highlighted
6. Mechanic confirms
7. Structured record is shown to office worker
8. Office worker checks/edits
9. Office worker enters it into WERBAS manually

MVP should NOT initially include

* Direct WERBAS integration
* Advanced computer vision
* Damage detection
* Automatic customer administration
* Complex workflow automation
* Fully autonomous data entry

The MVP should prove one thing:

Can we reliably turn 20–60 seconds of natural mechanic speech into a correct, structured tire-registration record?

⸻

Potential Technology Stack

A possible architecture:

Mobile / Tablet
      ↓
Web App
      ↓
Speech-to-Text
      ↓
LLM / Structured Extraction
      ↓
Validation Layer
      ↓
Database
      ↓
Office Web Interface
      ↓
Manual WERBAS Entry

Possible components:

* Frontend: simple web application
* Speech recognition: Whisper or comparable speech-to-text model
* AI extraction: structured LLM output
* Backend: Python / FastAPI or Node.js
* Database: PostgreSQL or SQLite for MVP
* Authentication: simple workshop user accounts
* Future integration: WERBAS API / REST / database interface

The exact technology should be selected after checking the requirements of the workshop environment.

⸻

Success Criteria

The project should be considered successful if it achieves:

Mechanic

* Very little typing
* No handwriting
* Registration possible while working
* ~30–60 seconds of documentation effort
* Simple confirmation workflow

Office worker

* Receives structured digital information
* Does not need to decipher handwriting
* Can correct individual fields quickly
* Can manually transfer information to WERBAS

Data quality

* Low transcription error rate
* No silent AI guesses
* Uncertain fields clearly marked
* Consistent tire sizes and measurements
* Correct distinction between front/rear measurements

⸻

Long-Term Vision

The system could evolve from a voice-assisted tire registration tool into a broader workshop intake platform.

                  WORKSHOP DIGITAL INTAKE
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
      Voice input      License plate      OCR
          │             recognition         │
          └────────────────┼────────────────┘
                           ↓
                    AI data extraction
                           ↓
                    Validation layer
                           ↓
                    Vehicle database
                           ↓
                    Office approval
                           ↓
                         WERBAS

The central philosophy remains:

The mechanic provides information once, in the fastest possible way. The system structures it, the office verifies it, and eventually the software receives it automatically.

⸻

Project Priority

Phase 1 — MVP

Voice → structured tire/vehicle data → office verification

Phase 2

Existing customer/vehicle lookup

Phase 3

License plate recognition + OCR

Phase 4

WERBAS API/integration

Phase 5

Further workshop automation

The project should start with voice registration, because that attacks the biggest source of wasted mechanic time without requiring a risky integration with WERBAS.