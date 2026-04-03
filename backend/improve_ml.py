import os
import pandas as pd
import random

# Base keywords for each category
categories = {
    "Food & Dining": [
        "Starbucks", "McDonald's", "Domino's Pizza", "Chipotle", "Subway", "Dunkin Donuts", "Pizza Hut", "KFC", "Taco Bell", 
        "Panera Bread", "Thai Restaurant", "Italian Bistro", "Sushi Bar", "Chinese Takeaway", "Indian Curry House", "Burger King", 
        "Wendy's", "Panda Express", "Five Guys", "Olive Garden", "Restaurant", "Coffee Shop", "Bakery", "Ice Cream", 
        "Smoothie King", "Breakfast Diner", "Lunch Cafe", "Food Court", "Doordash", "Uber Eats", "Grubhub", "Zomato", "Swiggy",
        "Peet's Coffee", "Shake Shack", "In-N-Out", "Chick-fil-A", "Sweetgreen", "Cava", "Local diner", "Food truck",
        "Papa Johns", "Jersey Mikes", "Jimmy Johns", "Sweet frog", "Cold Stone"
    ],
    "Transportation": [
        "Uber", "Lyft", "Shell", "BP Fuel", "Chevron", "Exxon", "Parking", "Toll", "Bus Pass", "Metro", "Train Ticket", 
        "Taxi", "Car Wash", "Oil Change", "Firestone", "Geico", "DMV", "Auto Repair", "Brake Service", "Car Battery", 
        "Parking Meter", "Airport Parking", "Uber Pool", "Lyft Shared", "Ola", "Rapido", "Metro Rail", "Railway", 
        "Flight Booking", "Car Rental", "Amtrak", "MTA", "BART", "Sunoco", "Speedway", "Valvoline", "Wawa Gas", 
        "QuikTrip", "Marathon Gas", "Mobil", "Texaco", "Progressive", "State Farm"
    ],
    "Shopping": [
        "Amazon", "Walmart", "Target", "Best Buy", "Apple Store", "Nike", "Zara", "H&M", "IKEA", "Home Depot", 
        "Costco", "Nordstrom", "Macy's", "Forever 21", "Gap", "Adidas", "Under Armour", "Lowe's", "Bed Bath Beyond", 
        "Wayfair", "Etsy", "eBay", "Flipkart", "Myntra", "Ajio", "Samsung", "Sony", "Book Store", "Gift Shop", 
        "Jewelry Store", "Watch Store", "Sephora", "Ulta", "Bath & Body Works", "TJ Maxx", "Marshalls", "HomeGoods",
        "Lululemon", "Victoria's Secret", "Dick's Sporting Goods", "Shein", "Temu", "Asos"
    ],
    "Bills & Utilities": [
        "Electric Bill", "Water Bill", "Gas Bill", "Comcast", "Verizon", "AT&T", "T-Mobile", "Spectrum", 
        "Electricity Board", "Municipal Water", "Broadband", "Jio", "Airtel", "BSNL", "Waste Management", 
        "Sewer Service", "Home Security", "Pest Control", "Lawn Care", "HVAC Maintenance", "Plumbing", 
        "Electrician", "Home Cleaning", "Laundry", "Property Tax", "HOA Dues", "ConEd", "PG&E", "Duke Energy", "Sprint", "Cox Communications",
        "Liberty Utilities", "Dominion Energy", "Xfinity", "Optimum", "ADT Security"
    ],
    "Entertainment": [
        "Movie Theater", "Netflix", "Concert Tickets", "Spotify", "AMC Cinema", "Bowling Alley", "Mini Golf", 
        "Amusement Park", "Zoo", "Museum", "Comedy Show", "Sports Event", "Video Game", "PlayStation Store", 
        "Xbox Game Pass", "Nintendo", "Disney Plus", "Hulu", "HBO Max", "Apple TV", "Theme Park", "Escape Room", 
        "Karaoke", "Bar", "Club Entry", "Board Game", "Arcade", "Trampoline Park", "Laser Tag", "Book Club", 
        "Regal Cinemas", "Ticketmaster", "StubHub", "Steam", "Epic Games", "Twitch", "Billiard", "Cinemark", "Eventbrite"
    ],
    "Health & Fitness": [
        "Doctor Visit", "Gym Membership", "Pharmacy", "Dentist", "Eye Doctor", "CVS", "Walgreens", "GNC", "Yoga Class", 
        "Personal Trainer", "Physical Therapy", "Mental Health", "Dermatologist", "Lab Test", "X-Ray", "Health Insurance", 
        "Dental Insurance", "Contact Lenses", "Protein Powder", "Running Shoes", "Fitness App", "Calm", "Spa", 
        "Chiropractor", "Urgent Care", "Hospital", "Surgery", "Ambulance", "Planet Fitness", "Equinox", "LA Fitness", "Peloton",
        "Anytime Fitness", "Crunch Fitness", "Rite Aid", "Kaiser Permanente", "Blue Cross"
    ],
    "Education": [
        "Udemy", "Coursera", "College Tuition", "Textbook", "School Supplies", "SAT Prep", "GRE Test", "TOEFL Exam", 
        "Coding Bootcamp", "Language App", "Skillshare", "LinkedIn Learning", "Khan Academy", "Tutoring", "Music Lessons", 
        "Art Class", "Conference", "Certification", "Library Fine", "Study Materials", "Notebook", "Laptop", 
        "Calculator", "Student Loan", "Scholarship", "Educational Software", "Duolingo", "Chegg", "Quizlet",
        "Sallie Mae", "Navient", "University", "College", "Bookstore"
    ],
    "Travel": [
        "Marriott", "Airbnb", "Hilton", "Delta", "United Airlines", "Southwest", "Hertz", "Travel Insurance", 
        "Passport", "Visa", "Samsonite", "Travel Adapter", "Airport Lounge", "International SIM", "Travel Vaccination", 
        "Carnival Cruise", "Tour Guide", "Hostel", "Resort", "Beach Equipment", "Ski Resort", "Hiking Gear", 
        "REI", "Road Trip", "Travel Photography", "Expedia", "Booking.com", "Kayak", "American Airlines", "JetBlue",
        "Spirit Airlines", "Enterprise Rent-A-Car", "Avis", "Budget", "Alamo", "Vrbo", "Hyatt", "Holiday Inn"
    ],
    "Subscriptions": [
        "Netflix", "Spotify", "Amazon Prime", "YouTube Premium", "Adobe", "Microsoft 365", "Dropbox", "iCloud", 
        "Google One", "Notion", "GitHub Pro", "ChatGPT Plus", "Grammarly", "NordVPN", "McAfee", "AWS", 
        "Domain Name", "Website Hosting", "Mailchimp", "Salesforce", "Slack", "Zoom", "Newspaper", "Magazine", 
        "HelloFresh", "Blue Apron", "Patreon", "Substack", "Medium", "Canva", "Dashlane", "1Password",
        "Hulu Premium", "Disney+", "Bumble", "Tinder", "Squarespace", "Wix", "Shopify"
    ],
    "Groceries": [
        "Walmart Grocery", "Kroger", "Whole Foods", "Trader Joe's", "Aldi", "Safeway", "Publix", "Costco Grocery", 
        "Target Grocery", "Fresh Fruits", "Vegetable Stand", "Meat Market", "Fish Market", "Bakery", "Dairy", 
        "Organic Food", "Asian Grocery", "Indian Grocery", "Mexican Grocery", "Farmers Market", "Bulk Food", 
        "Snacks", "Beverage", "Baby Food", "Pet Food", "Frozen Food", "Canned Goods", "Pasta", "Spices", "Cleaning Supplies",
        "Wegmans", "H-E-B", "Meijer", "Albertsons", "Sprouts Farmers Market", "Winn-Dixie", "Ralphs", "Vons", "Food Lion", "Stop & Shop"
    ],
    "Rent & Housing": [
        "Rent", "Mortgage", "Home Insurance", "Renter Insurance", "Security Deposit", "Property Management", 
        "Home Renovation", "Kitchen Remodel", "Bathroom Renovation", "Roof Repair", "Window Replacement", "Paint Supplies", 
        "Landscaping", "Moving Company", "Storage Unit", "Furniture Assembly", "Carpet Cleaning", "Appliance Repair", 
        "Smart Home Device", "Door Lock", "U-Haul", "Public Storage", "Extra Space Storage", "Apartment", "Leasing Office", 
        "HOA Fee", "Plumber", "Electrician Service", "Home Depot"
    ],
    "Income": [
        "Salary", "Freelance", "Consulting", "Dividend", "Stock Sale", "Rental Income", "Side Hustle", "Part Time Job", 
        "Bonus", "Commission", "Tax Refund", "Interest Income", "Cashback", "Gift Money", "Sold Items", "Tutoring Income", 
        "YouTube Ad Revenue", "Adsense", "Photography Gig", "Music Royalty", "Payroll", "Direct Deposit", "Venmo Deposit", "Zelle Transfer",
        "Cash App Transfer", "Stripe Payout", "PayPal Transfer", "Upwork", "Fiverr", "Uber Earnings"
    ],
    "Other": [
        "ATM", "Bank Fee", "Wire Transfer", "Currency Exchange", "Donation", "Tithe", "Political Contribution", 
        "Legal Fee", "Accounting", "Notary", "Passport Photo", "Dry Cleaning", "Tailoring", "Key Duplication", 
        "Shoe Repair", "Car Detailing", "Pet Grooming", "Veterinary", "Pet Supplies", "Daycare", "Babysitter", 
        "Birthday Party", "Wedding Gift", "Funeral Flowers", "Lottery Ticket", "Post Office", "FedEx", "UPS", "DHL",
        "USPS", "Charity", "GoFundMe", "Overdraft Fee", "Late Fee", "Maintenance Fee", "Parking Ticket", "Speeding Ticket"
    ]
}

prefixes = ["Payment to", "Purchase at", "Online order", "POS Transaction", "Debit Card", "Credit Card", "ACH", "Transfer to", ""]
suffixes = ["inc", "llc", "store", "shop", "online", "payment", ""]

data = []

# First, retain the original dataset to ensure pure cases exist
for cat, items in categories.items():
    for item in items:
        data.append({"description": item, "category": cat})
        data.append({"description": item.upper(), "category": cat})
        data.append({"description": item.lower(), "category": cat})

# Generate 5,000 synthetic transaction variations
for _ in range(5000):
    cat = random.choice(list(categories.keys()))
    base_name = random.choice(categories[cat])
    
    prefix = random.choice(prefixes)
    suffix = random.choice(suffixes)
    loc = f" #{random.randint(100, 9999)}" if random.random() > 0.7 else ""
    date_code = f" {random.randint(1,12)}/{random.randint(1,28)}" if random.random() > 0.8 else ""
    
    desc_parts = []
    if prefix and random.random() > 0.5:
        desc_parts.append(prefix)
    desc_parts.append(base_name)
    if suffix and random.random() > 0.7:
        desc_parts.append(suffix)
    if loc:
        desc_parts.append(loc)
    if date_code:
        desc_parts.append(date_code)
        
    desc = " ".join(desc_parts).strip()
    if random.random() > 0.5:
        desc = desc.upper()
    elif random.random() > 0.8:
        desc = desc.lower()
        
    data.append({"description": desc, "category": cat})

df = pd.DataFrame(data)

# Save to seed_transactions.csv
output_path = os.path.join("app", "ml", "training_data", "seed_transactions.csv")
df.to_csv(output_path, index=False)
print(f"Generated {len(df)} transactions and saved to {output_path}")

# Retrain the model
print("Retraining the ML model...")
from app.ml.categorizer import categorizer

# Delete old joblib to force clean state just in case
if os.path.exists(categorizer.model_path):
    os.remove(categorizer.model_path)
    
categorizer.train()
print(f"Model successfully retrained with {len(df)} samples! New accuracy: {categorizer.accuracy*100:.2f}%")
