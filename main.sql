-- 1 BASE INDEPENDENT TABLES (No Foreign Keys)(main tables)

CREATE TABLE Users (
    id CHAR(36) PRIMARY KEY, -- Using UUIDs for scalability
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20) UNIQUE,
    password VARCHAR(255) NOT NULL,
    profile_pic VARCHAR(255),
    national_id_verified BOOLEAN DEFAULT FALSE,
    role ENUM('donor', 'reviewer', 'admin', 'user') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Organizations (
    id CHAR(36) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    type ENUM('pharmacy', 'ngo', 'orphanage', 'elderly_home', 'hospital') NOT NULL,
    license_number VARCHAR(100) NOT NULL UNIQUE,
    verified BOOLEAN DEFAULT FALSE,
    address TEXT NOT NULL,
    phone VARCHAR(20) NOT NULL
);

CREATE TABLE Categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    type ENUM('medicine', 'equipment') NOT NULL
);

CREATE TABLE Advertisers (
    id CHAR(36) PRIMARY KEY,
    company_name VARCHAR(150) NOT NULL,
    type ENUM('pharma', 'medical_device', 'lab') NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL
);

-- 2 DEPENDENT TABLES (Level 1 Dependencies)

CREATE TABLE Requests (
    id CHAR(36) PRIMARY KEY,
    organization_id CHAR(36) NOT NULL,
    category_id INT NOT NULL,
    item_name VARCHAR(150) NOT NULL,
    quantity_needed INT NOT NULL CHECK (quantity_needed > 0),
    urgency ENUM('low', 'medium', 'high') NOT NULL,
    status ENUM('open', 'fulfilled', 'cancelled') DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES Organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES Categories(id) ON DELETE RESTRICT
);

CREATE TABLE Donations (
    id CHAR(36) PRIMARY KEY,
    donor_id CHAR(36) NOT NULL,
    category_id INT NOT NULL,
    type ENUM('medicine', 'equipment') NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    photo VARCHAR(255) NOT NULL,
    location VARCHAR(255)NOT NULL,
    status ENUM('pending_review', 'approved', 'rejected', 'matched', 'delivered') DEFAULT 'pending_review',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donor_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES Categories(id) ON DELETE RESTRICT
);

CREATE TABLE AdCampaigns (
    id CHAR(36) PRIMARY KEY,
    advertiser_id CHAR(36) NOT NULL,
    ad_content TEXT NOT NULL,
    placement VARCHAR(50) NOT NULL, 
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    budget DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (advertiser_id) REFERENCES Advertisers(id) ON DELETE CASCADE
);

-- 3. SPECIFIC SUB-DETAILS & INSPECTIONS (Level 2 Dependencies)

-- 1:1 Relationship table for Medicine details
CREATE TABLE MedicineDetails (
    donation_id CHAR(50) PRIMARY KEY,
    expiry_date DATE NOT NULL,
    batch_number VARCHAR(100),
    manufacturer VARCHAR(150),
    dosage_form VARCHAR(100), -- Tablet, Syrup
    FOREIGN KEY (donation_id) REFERENCES Donations(id) ON DELETE CASCADE
);

-- 1:1 Relationship table for Equipment details
CREATE TABLE EquipmentDetails (
    donation_id CHAR(50) PRIMARY KEY,
    `condition` ENUM('new', 'used_good', 'needs_repair') NOT NULL,
    needs_maintenance BOOLEAN DEFAULT FALSE,
    maintenance_notes TEXT,
    FOREIGN KEY (donation_id) REFERENCES Donations(id) ON DELETE CASCADE
);

CREATE TABLE Inspections (
    id CHAR(36) PRIMARY KEY,
    donation_id CHAR(36) NOT NULL,
    inspector_id CHAR(36) NOT NULL, 
    result ENUM('approved', 'rejected', 'needs_maintenance') NOT NULL,
    notes TEXT,
    inspected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donation_id) REFERENCES Donations(id) ON DELETE CASCADE,
    FOREIGN KEY (inspector_id) REFERENCES Users(id) ON DELETE RESTRICT
);

-- 4. MATCHING & LOGISTICS (Level 3 & 4 Dependencies)

CREATE TABLE Matches (
    id CHAR(36) PRIMARY KEY,
    donation_id CHAR(36) NOT NULL,
    request_id CHAR(36) NOT NULL,
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    FOREIGN KEY (donation_id) REFERENCES Donations(id) ON DELETE RESTRICT,
    FOREIGN KEY (request_id) REFERENCES Requests(id) ON DELETE RESTRICT
);

-- 1:1 Relationship table mapping a delivery to a specific match
CREATE TABLE Deliveries (
    id CHAR(36) PRIMARY KEY,
    match_id CHAR(36) NOT NULL UNIQUE,
    courier_name VARCHAR(100),
    pickup_date DATETIME,
    delivery_date DATETIME,
    status ENUM('assigned', 'in_transit', 'delivered', 'failed') DEFAULT 'assigned',
    FOREIGN KEY (match_id) REFERENCES Matches(id) ON DELETE CASCADE
);

