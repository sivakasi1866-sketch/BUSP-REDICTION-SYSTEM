============================================================
PARTNERS BUS PREDICTION
MASTER PROJECT REQUIREMENTS
============================================================

PROJECT NAME:
Partners Bus Prediction

PROJECT TYPE:
Responsive Web-Based Smart College Bus Tracking, Management,
ETA Prediction and Notification System.

============================================================
1. PROJECT PURPOSE
============================================================

Partners Bus Prediction is a complete web-based college bus
management and prediction system.

The system must provide separate role-based experiences for:

- Admin
- Driver
- Student
- Staff

The system must manage:

- Users
- Students
- Staff
- Drivers
- Buses
- Routes
- Stops
- Assignments
- Trips
- Bus GPS tracking
- ETA prediction
- Notifications
- Fleet monitoring
- Reports
- Bulk data import

The system must be usable through a web browser and must be
responsive for:

- Desktop
- Laptop
- Tablet
- Mobile phone

============================================================
2. MAIN PROJECT PRINCIPLE
============================================================

The main principle is:

TRACK THE BUS, NOT THE STUDENT.

The system must track the college bus during an active trip.

The system must NOT track the live location of students or staff.

============================================================
3. COST REQUIREMENT
============================================================

The project must follow:

₹0 / FREE-TIER-FIRST

The target operating cost is ₹0 wherever practically possible.

The project must prioritize:

- Free services
- Free tiers
- Open-source software
- Open datasets
- Local solutions
- Self-hosted solutions where practical
- Free infrastructure
- Free APIs where suitable

The project must avoid unnecessary:

- Paid APIs
- Paid AI services
- Paid map services
- Paid SMS services
- Paid notification services
- Paid databases
- Paid storage
- Paid hosting
- Paid third-party services

No paid service should become a required dependency without
explicit approval.

Free-tier quotas and limitations must be respected.

The system must not accidentally generate paid usage.

============================================================
4. PRIVACY REQUIREMENTS
============================================================

Privacy is a core requirement.

The system must NEVER collect or track live GPS/location of:

- Students
- Staff
- Teachers
- Passengers

The system must never require student GPS permission.

The system must never require staff GPS permission.

The system must never create hidden background location tracking.

The system must never store student live-location history.

The system must never store staff live-location history.

Student and staff services must work without their live GPS.

Bus-stop coordinates represent fixed infrastructure locations.

Bus-stop coordinates must never represent student or staff
locations.

============================================================
5. DRIVER GPS REQUIREMENT
============================================================

Only the driver's device may provide live bus GPS.

Driver GPS must be TRIP-SCOPED.

Required behavior:

Driver Login
↓
Assigned Bus
↓
Start Trip
↓
GPS Tracking ON
↓
Bus Movement
↓
GPS Updates
↓
ETA Prediction
↓
Stop Trip
↓
GPS Tracking OFF

Before Start Trip:

GPS tracking must be OFF.

During an active trip:

GPS tracking may be ON.

After Stop Trip:

GPS tracking must immediately stop.

GPS must not continue after the trip ends.

Every GPS record must be associated with the appropriate trip.

============================================================
6. USER ROLES
============================================================

The system must contain four primary roles:

1. ADMIN
2. DRIVER
3. STUDENT
4. STAFF

Each role must have appropriate permissions.

============================================================
7. ADMIN REQUIREMENTS
============================================================

Admin must be able to manage the complete bus system.

Admin must be able to manage:

- Students
- Staff
- Drivers
- Buses
- Routes
- Stops
- Assignments
- Trips
- Fleet monitoring
- Reports
- Bulk imports
- Special assignments
- Exam-day assignments

Admin must have a dashboard containing fleet-wide information.

============================================================
8. DRIVER REQUIREMENTS
============================================================

Driver must be able to:

- Login
- View assigned bus
- View assigned route
- View trip information
- Start Trip
- Send bus GPS during an active trip
- View GPS/trip status
- View relevant route information
- Stop Trip

The driver must clearly know whether GPS tracking is active.

The driver must not be able to operate unauthorized trips.

============================================================
9. STUDENT REQUIREMENTS
============================================================

Student must be able to:

- Login
- View own account information
- View allocated bus
- View allocated stop
- View route information
- View bus status
- View ETA
- Receive arrival notifications

Student must not be able to:

- View another student's private information
- View student GPS
- View staff GPS
- Access admin functions
- Access internal system information

============================================================
10. STAFF REQUIREMENTS
============================================================

Staff must be able to:

- Login
- View permitted bus information
- View permitted route information
- View ETA
- View bus status
- Receive relevant notifications

Staff must not be tracked through GPS.

============================================================
11. USER MANAGEMENT
============================================================

Admin must be able to manage:

STUDENTS:

- Create
- View
- Update
- Deactivate

STAFF:

- Create
- View
- Update
- Deactivate

DRIVERS:

- Create
- View
- Update
- Deactivate

Passwords must never be returned through APIs.

Passwords must never be stored as plaintext.

============================================================
12. BUS MANAGEMENT
============================================================

The system must support:

- Create bus
- View buses
- View bus details
- Update bus
- Deactivate bus
- Reactivate bus
- Bus capacity
- Bus identifier
- Driver assignment
- Route assignment where required
- Bus status

Bus identifiers must be unique.

Bus capacity must be validated.

Inactive buses must not accidentally be used as active buses.

============================================================
13. ROUTE MANAGEMENT
============================================================

The system must support:

- Create route
- View routes
- View route details
- Update route
- Manage route stops
- Maintain stop sequence
- View stop count

Stop ordering must remain correct.

Example:

Stop 1
↓
Stop 2
↓
Stop 3
↓
Stop 4

============================================================
14. STOP MANAGEMENT
============================================================

Each stop must support appropriate information such as:

- Stop name
- Latitude
- Longitude
- Sequence
- Active/inactive status
- Route relationship

Latitude must be between:

-90 and +90

Longitude must be between:

-180 and +180

Stop coordinates must represent fixed bus-stop locations.

============================================================
15. ASSIGNMENT MANAGEMENT
============================================================

The system must support:

- Bus assignment
- Driver assignment
- Student assignment
- Staff assignment
- Default assignments
- Special assignments
- Exam-day assignments

Assignments must be controlled by appropriate permissions.

Historical assignments must not unnecessarily destroy historical
trip information.

============================================================
16. TRIP MANAGEMENT
============================================================

The system must support:

- Trip creation/management
- Assigned bus
- Assigned driver
- Assigned route
- Start time
- End time
- Trip status
- GPS information
- Stop progress
- ETA
- Historical trip information

Trip states may include:

- NOT_STARTED
- ACTIVE
- COMPLETED
- CANCELLED

============================================================
17. GPS DATA REQUIREMENTS
============================================================

Bus GPS information may include:

- Trip ID
- Timestamp
- Latitude
- Longitude
- Speed
- Accuracy
- Required telemetry

GPS data must belong to the active trip.

GPS updates without an active trip must not be treated as
active bus tracking.

GPS data must never be associated with student/staff locations.

============================================================
18. LIVE BUS TRACKING
============================================================

The system must provide live bus information during active trips.

The system should be able to display:

- Current bus position
- Current route
- Route progress
- Passed stops
- Upcoming stops
- Trip status
- ETA

Live bus tracking must stop when the trip ends.

============================================================
19. MAP REQUIREMENTS
============================================================

The web application must provide map visualization for:

- Bus location
- Routes
- Stops
- Trip progress
- ETA information

The map must never show:

- Student live locations
- Staff live locations
- Passenger live locations

Open/free map data should be preferred.

When OpenStreetMap services are used, their current usage and
attribution requirements must be respected. The public OSM tile
servers are not an unlimited free tile API; visible attribution,
appropriate caching and responsible usage are required. 0

============================================================
20. ETA PREDICTION
============================================================

The system must provide bus ETA.

ETA may consider:

- Current bus position
- Remaining distance
- Current speed
- Remaining stops
- Scheduled travel time
- Historical travel data
- Time of day
- Day of week
- Peak-hour information
- Route characteristics
- Other valid operational information

ETA must distinguish between:

- Scheduled time
- Calculated ETA
- ML-predicted ETA
- Actual arrival time

============================================================
21. MACHINE LEARNING
============================================================

The project must support machine-learning-based ETA prediction.

ML workflow:

Data
↓
Cleaning
↓
Feature Engineering
↓
Training
↓
Validation
↓
Evaluation
↓
Model
↓
Prediction
↓
ETA

Possible features include:

- distance_km
- speed_kmh
- stop_count_remaining
- scheduled_travel_min
- theoretical_minutes
- time_sin
- time_cos
- day_sin
- day_cos
- is_peak_hour
- log_distance

Model performance must be measured.

Possible evaluation metrics:

- MAE
- RMSE
- R²
- ETA error
- Arrival-time error

ML accuracy must not be claimed without testing.

============================================================
22. EXISTING ETA BASELINE
============================================================

An existing project baseline has been evaluated approximately as:

MAE:
4.72

RMSE:
5.88

R²:
0.2980

These are historical project measurements.

They are not guaranteed production accuracy.

Future models must be evaluated again using appropriate data.

============================================================
23. DATASET REQUIREMENTS
============================================================

The system may use:

- Historical trip data
- Static route data
- Static stop data
- Schedule data
- Simulated GPS data
- Synthetic training data
- Public transportation data
- Real operational data where legally and appropriately
  available

Synthetic data must always be identified as synthetic.

Simulated GPS must always be identified as simulated.

Synthetic results must never be presented as real-world results.

============================================================
24. NOTIFICATION REQUIREMENTS
============================================================

The system must support bus arrival notifications.

Required thresholds:

ETA ≤ 10 minutes
ETA ≤ 5 minutes
ETA ≤ 2 minutes
ETA = 0 / Arrived

Notifications must avoid duplicates.

Example:

12 minutes
→ No arrival notification

9 minutes
→ 10-minute notification

7 minutes
→ No duplicate notification

4 minutes
→ 5-minute notification

1 minute
→ 2-minute notification

0 minutes
→ Arrived notification

============================================================
25. ADMIN DASHBOARD
============================================================

The web application must contain an Admin Dashboard.

The dashboard must provide fleet-wide information.

It should include:

- Total buses
- Active buses
- Inactive buses
- Active trips
- Completed trips
- Drivers
- Routes
- Stops
- Students
- Staff
- Current bus status
- Trip status
- ETA information
- Alerts
- Recent trips
- Reports

The dashboard must provide clear management and monitoring.

============================================================
26. REPORTS
============================================================

The system must support reports such as:

- Daily trip reports
- Bus utilization
- Route performance
- Stop arrival information
- ETA accuracy
- Trip history
- Assignment reports
- Import reports
- Historical trends

Reports must follow role permissions and privacy requirements.

============================================================
27. EXCEL BULK IMPORT
============================================================

Admin must be able to import multiple records.

Supported records:

- Students
- Staff
- Drivers

Required workflow:

Upload
↓
Validation
↓
Preview
↓
Confirmation
↓
Import
↓
Result

Validation must detect:

- Missing fields
- Invalid fields
- Duplicate records
- Existing database conflicts
- Invalid headers
- Invalid formats
- Unsupported fields
- Oversized files

Student/staff live-location or GPS fields must not be accepted.

============================================================
28. AUTHENTICATION
============================================================

The system must provide secure authentication.

Requirements:

- Login
- Secure password hashing
- Authentication tokens/sessions
- Token expiration
- Invalid-token rejection
- Protected endpoints
- Role-based access

Passwords must never be:

- Stored in plaintext
- Returned by APIs
- Logged
- Exposed in frontend code

============================================================
29. ROLE-BASED ACCESS CONTROL
============================================================

Authorization must be enforced by the backend.

ADMIN:

Full management permissions according to system rules.

DRIVER:

Only authorized driver/trip operations.

STUDENT:

Only permitted student information.

STAFF:

Only permitted staff information.

Frontend hiding alone must not be considered security.

============================================================
30. DATABASE
============================================================

The system must maintain a relational database.

Core entities include:

- Users
- Students
- Staff
- Drivers
- Buses
- Routes
- Stops
- Default Assignments
- Special Assignments
- Route/Stop/Bus mappings
- Trips
- GPS Pings
- Stop Events
- Notifications
- Import information

Existing database architecture must be preserved.

A second independent database must not be created unnecessarily.

Duplicate models for the same entity must not be created
unnecessarily.

Historical records must remain meaningful.

Foreign-key relationships must remain valid.

============================================================
31. SECURITY
============================================================

The system must protect:

- Passwords
- Authentication tokens
- Database credentials
- API credentials
- Personal information
- GPS information
- Uploaded files
- Sensitive configuration

Secrets must not be committed to source control.

Credentials must not be exposed in frontend code.

============================================================
32. API REQUIREMENTS
============================================================

APIs must provide:

- Authentication
- Authorization
- Input validation
- Consistent responses
- Correct status codes
- Secure error handling
- Documentation
- Testing

Existing API architecture must be preserved.

Duplicate endpoints must not be unnecessarily created.

============================================================
33. ERROR HANDLING
============================================================

The system must safely handle:

- Invalid login
- Expired token
- Unauthorized access
- Invalid bus
- Invalid route
- Invalid stop
- Invalid assignment
- Invalid GPS
- Missing active trip
- Invalid Excel
- Duplicate data
- Database errors
- ETA unavailable

Internal stack traces and secrets must not be exposed to normal
users.

============================================================
34. WEB APPLICATION
============================================================

The main system must be a responsive web application.

The website must provide separate dashboards/interfaces for:

ADMIN
- Admin Dashboard
- Fleet Management
- User Management
- Bus Management
- Route Management
- Stop Management
- Assignment Management
- Trip Management
- Reports
- Monitoring

DRIVER
- Driver Dashboard
- Assigned Bus
- Assigned Route
- Start Trip
- Active Trip
- GPS Status
- Stop Trip

STUDENT
- Student Dashboard
- Allocated Bus
- Allocated Stop
- Bus Status
- ETA
- Notifications

STAFF
- Staff Dashboard
- Permitted Bus Information
- Route Information
- ETA
- Notifications

The website must be usable on mobile, tablet, laptop and desktop.

============================================================
35. FRONTEND REQUIREMENTS
============================================================

The interface must be:

- Responsive
- Simple
- Clear
- Mobile-friendly
- Easy to navigate
- Role-specific
- Accessible
- Consistent

Admin screens may contain detailed management features.

Driver screens must prioritize operational simplicity.

Student screens must prioritize bus and ETA information.

Staff screens must prioritize permitted operational information.

============================================================
36. TESTING
============================================================

The project must include testing for:

- Authentication
- RBAC
- Database
- User management
- Excel import
- Bus management
- Route management
- Stop management
- Assignment management
- Trip management
- GPS
- ETA
- Machine learning
- Notifications
- Security
- Privacy
- Regression

Every major modification must be tested.

Existing functionality must be regression-tested after changes.

============================================================
37. PRIVACY TESTING
============================================================

Testing must verify that:

- Students have no live GPS tracking
- Staff have no live GPS tracking
- Student GPS is not stored
- Staff GPS is not stored
- GPS is associated with trips
- GPS stops after Stop Trip
- Unauthorized users cannot access GPS information
- Student/staff location fields are not introduced accidentally

============================================================
38. COST CONTROL
============================================================

Every external service must be evaluated against the ₹0
requirement.

The project must prefer:

- Free tier
- Open source
- Local implementation
- Self-hosted implementation
- Free public datasets
- Free infrastructure

The project must avoid unnecessary recurring costs.

No hidden paid dependency should be introduced.

============================================================
39. DEVELOPMENT ROADMAP
======================================================