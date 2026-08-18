import os
from datetime import datetime, timedelta, timezone
from app import create_app
from app.models import db, User, Category, Project, ProjectImage, Conversation, Message, Notification, Review, ContactMessage
from app.services.auth_service import slugify

def seed_database(app=None):
    if app is None:
        app = create_app('development')
    
    with app.app_context():
        db.create_all()

        categories_data = [
            ("AI & Machine Learning", "fa-brain", "Computer vision, NLP, edge AI, model optimization and dataset pipelines."),
            ("Web Development", "fa-code", "Full-stack web applications, REST APIs, frontend frameworks, and cloud hosting."),
            ("Mobile Development", "fa-mobile-screen", "Native and cross-platform iOS & Android apps, BLE integration, and UX."),
            ("Electronics", "fa-bolt", "PCB schematics, power supplies, analog circuits, and component soldering."),
            ("Embedded Systems", "fa-microchip", "Microcontroller firmware, RTOS, ARM Cortex, and low-level drivers."),
            ("IoT", "fa-wifi", "Connected sensors, MQTT, cloud telemetry, ESP32, and smart home modules."),
            ("Arduino", "fa-memory", "Prototyping, sensor shields, C/C++ sketches, and actuator controllers."),
            ("Raspberry Pi", "fa-cubes", "Single-board computing, Linux automation, camera modules, and home servers."),
            ("Robotics", "fa-robot", "Autonomous rovers, robotic arms, kinematics, motor drivers, and ROS2."),
            ("Automation", "fa-gears", "PLC logic, industrial control, smart relays, and automated test benches."),
            ("Mechanical", "fa-wrench", "3D printing, CAD design, CNC fabrication, gearboxes, and chassis mechanics."),
            ("Electrical", "fa-plug", "High-voltage circuits, battery management systems (BMS), motors, and inverters."),
            ("Civil", "fa-building", "Structural models, GIS mapping, survey automation, and smart infrastructure."),
            ("Research", "fa-flask", "Academic prototypes, scientific instruments, data analysis, and laboratory tools."),
            ("College Projects", "fa-graduation-cap", "Engineering capstones, hackathon prototypes, and senior design builds."),
            ("Other", "fa-folder-open", "Multidisciplinary experiments, artistic installations, and niche inventions.")
        ]

        cat_map = {}
        for name, icon, desc in categories_data:
            slug = slugify(name)
            cat = Category.query.filter_by(slug=slug).first()
            if not cat:
                cat = Category(name=name, slug=slug, icon=icon, description=desc)
                db.session.add(cat)
                db.session.flush()
            cat_map[name] = cat

        # 1. Admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@secondspark.com',
                full_name='SecondSpark Admin',
                bio='Platform Administrator and community moderator.',
                skills='System Architecture, Moderation, Python, Flask',
                location='Global',
                role='admin'
            )
            admin.set_password('Admin@12345')
            db.session.add(admin)
            db.session.flush()

        # 2. Alex Chen
        alex = User.query.filter_by(username='alex_chen').first()
        if not alex:
            alex = User(
                username='alex_chen',
                email='alex@secondspark.com',
                full_name='Alex Chen',
                bio='Robotics hardware tinkerer and mechanical prototyping enthusiast with 4 years experience in ROS2 and 3D printing.',
                skills='Robotics, ROS2, C++, 3D Printing, Python',
                location='San Francisco, CA',
                role='user'
            )
            alex.set_password('Alex@12345')
            db.session.add(alex)
            db.session.flush()

        # 3. Priya Sharma
        priya = User.query.filter_by(username='priya_sharma').first()
        if not priya:
            priya = User(
                username='priya_sharma',
                email='priya@secondspark.com',
                full_name='Priya Sharma',
                bio='Embedded systems developer specializing in ESP32 firmware, BLE communication, and low-power IoT telemetry.',
                skills='ESP32, Embedded C, MQTT, FreeRTOS, PCB Design',
                location='Bangalore, India',
                role='user'
            )
            priya.set_password('Priya@12345')
            db.session.add(priya)
            db.session.flush()

        # 4. Marcus Vance
        marcus = User.query.filter_by(username='marcus_vance').first()
        if not marcus:
            marcus = User(
                username='marcus_vance',
                email='marcus@secondspark.com',
                full_name='Marcus Vance',
                bio='Computer Vision & AI engineer passionate about deploying lightweight YOLO and TensorFlow models to edge accelerators.',
                skills='Computer Vision, PyTorch, Jetson Nano, Python, OpenCV',
                location='Austin, TX',
                role='user'
            )
            marcus.set_password('Marcus@12345')
            db.session.add(marcus)
            db.session.flush()

        # 5. Elena Rostova
        elena = User.query.filter_by(username='elena_rostova').first()
        if not elena:
            elena = User(
                username='elena_rostova',
                email='elena@secondspark.com',
                full_name='Elena Rostova',
                bio='Biomedical engineer and CAD designer building low-cost assistive prosthetics and rehabilitation robotics.',
                skills='SolidWorks, Biomechanics, EMG Sensors, Arduino, C++',
                location='Berlin, Germany',
                role='user'
            )
            elena.set_password('Elena@12345')
            db.session.add(elena)
            db.session.flush()

        db.session.commit()

        sample_projects = [
            {
                "owner": alex,
                "category": cat_map["Robotics"],
                "title": "Autonomous LiDAR Lawn Mower with RTK-GPS Navigation",
                "short_summary": "Differential drive rover chassis built with brushless motors, running RPLiDAR A1 and ROS2 Humble navigation stack.",
                "description": "I began building an autonomous robotic lawn mower during the summer. The hardware platform is fully assembled with dual 24V BLDC geared hub motors, ODrive motor controller, emergency stop relays, and an RPLiDAR A1 sensor mounted on an aluminum extrusion frame.\n\nThe mechanical assembly is 90% complete and cuts grass when operated via RC transmitter. However, the autonomous SLAM and obstacle avoidance in ROS2 are crashing when processing point clouds.",
                "current_condition": "Incomplete",
                "problems_faults": "The robot drifts off path by 40-50cm because wheel odometry slips on wet grass. In addition, the ROS2 Nav2 node fails to compute local costmaps in real-time when the mower encounters tall weed patches, causing the navigation node to abort.",
                "help_required": "Looking for a robotics software engineer to fuse wheel odometry with an IMU via robot_localization EKF filter, and tune Nav2 costmap parameters for outdoor terrain.",
                "required_skills": "ROS2, Nav2, C++, IMU Sensor Fusion, Linux",
                "budget": 350.0,
                "budget_type": "Fixed",
                "location": "Remote / San Francisco",
                "deadline": "3 weeks",
                "status": "Help Needed",
                "is_featured": True
            },
            {
                "owner": priya,
                "category": cat_map["IoT"],
                "title": "Smart Greenhouse Hydroponic Controller with AWS IoT Core",
                "short_summary": "ESP32-based automated dosing and climate regulation system with pH, EC, temperature, and water level monitoring.",
                "description": "An automated hydroponics monitoring board designed around the ESP32-WROOM-32E module. It connects to 4 peristaltic dosing pumps, an analog pH sensor, a conductivity sensor probe, and a DHT22 ambient temperature sensor.\n\nThe board layout was fabricated and powers on cleanly. It has an OLED status display and can read basic sensor values.",
                "current_condition": "Hardware Issues",
                "problems_faults": "When the 12V peristaltic dosing pumps trigger via the on-board MOSFET switches, severe inductive voltage spikes backfeed into the 3.3V logic rail, causing the ESP32 to brownout reset. Also, the analog pH probe readings fluctuate wildly when the conductivity sensor is active in the same water reservoir.",
                "help_required": "Need an electronics engineer to assist with flyback diode snubbing, ground isolation circuitry, and optocoupler protection between pump drivers and microcontroller.",
                "required_skills": "PCB Design, Analog Electronics, ESP32, Noise Filtering",
                "budget": 200.0,
                "budget_type": "Fixed",
                "location": "Remote",
                "deadline": "2 weeks",
                "status": "Open",
                "is_featured": True
            },
            {
                "owner": elena,
                "category": cat_map["Electronics"],
                "title": "Low-Cost Bionic Hand with EMG Muscle Sensors",
                "short_summary": "3D-printed 5-finger prosthetic hand powered by SG90 micro servos and dual-channel surface EMG electrodes.",
                "description": "This project aims to build an accessible, open-source 3D-printed bionic hand for amputees under $150. All mechanical fingers use tendon-driven nylon lines with elastic returns.\n\nThe mechanical hand flexes smoothly when manually pulling strings. The dual-channel MyoWare EMG muscle sensor shield is wired to an Arduino Nano.",
                "current_condition": "Faulty",
                "problems_faults": "The surface EMG signal suffers from 50Hz/60Hz mains noise and erratic spikes whenever the user moves their arm slightly. The servo motors twitch uncontrollably instead of performing smooth grip and pinch gestures.",
                "help_required": "Assistance needed implementing a digital bandpass filter and moving average thresholding algorithm in Arduino C++ to convert noisy raw muscle signals into smooth servo positions.",
                "required_skills": "Signal Processing, Arduino, C++, DSP, Biomechanics",
                "budget": 280.0,
                "budget_type": "Fixed",
                "location": "Berlin / Remote",
                "deadline": "1 month",
                "status": "In Discussion",
                "is_featured": True
            },
            {
                "owner": marcus,
                "category": cat_map["AI & Machine Learning"],
                "title": "Edge AI Wildlife Camera Trap with Solar Power Harvest",
                "short_summary": "Nvidia Jetson Orin Nano camera trap with thermal trigger and on-device YOLOv8 animal classification.",
                "description": "An off-grid camera trap designed for forest conservation to detect endangered mammals. Uses an IP67 waterproof enclosure, wide-angle CSI camera, PIR thermal sensor, and solar charge controller.\n\nThe custom YOLOv8 model achieves 94% mAP on target species in PyTorch on a desktop workstation.",
                "current_condition": "Incomplete",
                "problems_faults": "The Jetson Orin Nano consumes too much standby power (around 4.5W idle) for a small 20W solar panel during cloudy periods. We need an ultra-low power MCU (like an ATtiny85) to power-gate the Jetson and wake it up only when the PIR sensor detects body heat.",
                "help_required": "Need someone to build a reliable power-gating circuit and write the wake/sleep handshake script over UART.",
                "required_skills": "Jetson Nano, Low Power Design, Python, PyTorch, Hardware Power Gating",
                "budget": 450.0,
                "budget_type": "Fixed",
                "location": "Remote",
                "deadline": "Flexible",
                "status": "Open",
                "is_featured": True
            },
            {
                "owner": alex,
                "category": cat_map["Automation"],
                "title": "Gesture-Controlled 6-DOF Robotic Arm with Inverse Kinematics",
                "short_summary": "Laser-cut acrylic 6-axis arm with NEMA 17 stepper motors and leap-motion gesture tracking.",
                "description": "A desktop educational robotic arm for automated pick-and-place tasks. Stepper motor drivers (TMC2209) provide quiet operation on a RAMPS 1.4 board.",
                "current_condition": "Faulty",
                "problems_faults": "The geometric inverse kinematics equation causes gimbal lock and sudden violent arm spins when crossing the Z-axis singularity points.",
                "help_required": "Implement numerical Jacobian-based inverse kinematics or Damped Least Squares (DLS) solver in Python to smoothly avoid singularities.",
                "required_skills": "Inverse Kinematics, Python, Robotics, Mathematics, CAD",
                "budget": 250.0,
                "budget_type": "Fixed",
                "location": "Remote",
                "deadline": "2 weeks",
                "status": "Completed",
                "is_featured": False
            }
        ]

        for p_data in sample_projects:
            slug = slugify(p_data["title"])
            existing = Project.query.filter_by(slug=slug).first()
            if not existing:
                proj = Project(
                    user_id=p_data["owner"].id,
                    category_id=p_data["category"].id,
                    title=p_data["title"],
                    slug=slug,
                    short_summary=p_data["short_summary"],
                    description=p_data["description"],
                    current_condition=p_data["current_condition"],
                    problems_faults=p_data["problems_faults"],
                    help_required=p_data["help_required"],
                    required_skills=p_data["required_skills"],
                    budget=p_data["budget"],
                    budget_type=p_data["budget_type"],
                    location=p_data["location"],
                    deadline=p_data["deadline"],
                    status=p_data["status"],
                    is_featured=p_data["is_featured"],
                    views_count=24
                )
                db.session.add(proj)
                db.session.flush()

                p_img = ProjectImage(
                    project_id=proj.id,
                    image_url='/static/images/project-placeholder.svg',
                    is_primary=True
                )
                db.session.add(p_img)

        db.session.commit()

        conv = Conversation.query.first()
        if not conv and alex and priya:
            first_proj = Project.query.first()
            now = datetime.now(timezone.utc)
            conv = Conversation(
                user1_id=priya.id,
                user2_id=alex.id,
                project_id=first_proj.id if first_proj else None,
                last_message="I have experience tuning Nav2 EKF filters on farm robots!",
                last_message_at=now - timedelta(hours=2)
            )
            db.session.add(conv)
            db.session.flush()

            m1 = Message(
                conversation_id=conv.id,
                sender_id=priya.id,
                receiver_id=alex.id,
                content="Hi Alex! I saw your LiDAR Lawn Mower project. I've tuned Nav2 EKF filters on farm rovers and would love to help fix your costmap drift.",
                is_read=True,
                created_at=now - timedelta(hours=2)
            )
            m2 = Message(
                conversation_id=conv.id,
                sender_id=alex.id,
                receiver_id=priya.id,
                content="That would be incredible, Priya! Are you familiar with fusing BNO085 IMU data with ODrive wheel encoder ticks?",
                is_read=True,
                created_at=now - timedelta(hours=1, minutes=40)
            )
            db.session.add_all([m1, m2])

            if first_proj:
                rev = Review(
                    project_id=first_proj.id,
                    reviewer_id=priya.id,
                    reviewee_id=alex.id,
                    rating=5,
                    comment="Great project collaboration! Clear schematics and well-documented ROS2 workspace.",
                    created_at=now - timedelta(days=1)
                )
                db.session.add(rev)

            db.session.commit()

if __name__ == '__main__':
    seed_database()
