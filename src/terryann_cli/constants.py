"""Shared constants for TerryAnn CLI.

Centralizes campaign types, icons, and other configuration values
that are used across multiple modules.
"""

# Campaign types available for journey creation
CAMPAIGN_TYPES = [
    ("aep_acquisition", "AEP Acquisition", "New enrollments during Annual Enrollment (Oct 15 - Dec 7)"),
    ("aep_retention", "AEP Retention", "Keeping current members during AEP"),
    ("turning_65", "Turning 65", "New-to-Medicare (Initial Enrollment Period)"),
    ("dsnp", "D-SNP", "Dual Eligible Special Needs Plans (Medicare + Medicaid)"),
    ("oep_retention", "OEP Retention", "Open Enrollment Period retention"),
    ("sep_acquisition", "SEP Acquisition", "Special Enrollment Period acquisition"),
    ("winback", "Winback", "Re-engaging lapsed members"),
]

# National archetypes (from geography_loader.py)
NATIONAL_ARCHETYPES = [
    ("nat_urban_coastal_affluent", "Urban Coastal Affluent",
     "High-income coastal metros, digitally-savvy seniors"),
    ("nat_diverse_urban", "Diverse Urban",
     "Multicultural neighborhoods, high language diversity"),
    ("nat_hispanic_border", "Hispanic Border & Gateway",
     "Spanish-dominant border communities and gateway cities"),
    ("nat_suburban_middle", "Suburban Middle America",
     "Middle-income heartland and Sun Belt suburbs"),
    ("nat_sun_belt_retiree", "Sun Belt Retiree",
     "Planned retirement communities in FL, AZ, Southwest"),
    ("nat_rural_agricultural", "Rural Agricultural",
     "Farming communities in Midwest and Great Plains"),
    ("nat_rural_appalachian", "Rural Appalachian",
     "Appalachian and rural Eastern, limited healthcare access"),
    ("nat_rust_belt", "Rust Belt Industrial",
     "Former industrial cities in Midwest and Northeast"),
]

# US States for selection
US_STATES = [
    ("AL", "Alabama"), ("AK", "Alaska"), ("AZ", "Arizona"), ("AR", "Arkansas"),
    ("CA", "California"), ("CO", "Colorado"), ("CT", "Connecticut"), ("DE", "Delaware"),
    ("FL", "Florida"), ("GA", "Georgia"), ("HI", "Hawaii"), ("ID", "Idaho"),
    ("IL", "Illinois"), ("IN", "Indiana"), ("IA", "Iowa"), ("KS", "Kansas"),
    ("KY", "Kentucky"), ("LA", "Louisiana"), ("ME", "Maine"), ("MD", "Maryland"),
    ("MA", "Massachusetts"), ("MI", "Michigan"), ("MN", "Minnesota"), ("MS", "Mississippi"),
    ("MO", "Missouri"), ("MT", "Montana"), ("NE", "Nebraska"), ("NV", "Nevada"),
    ("NH", "New Hampshire"), ("NJ", "New Jersey"), ("NM", "New Mexico"), ("NY", "New York"),
    ("NC", "North Carolina"), ("ND", "North Dakota"), ("OH", "Ohio"), ("OK", "Oklahoma"),
    ("OR", "Oregon"), ("PA", "Pennsylvania"), ("RI", "Rhode Island"), ("SC", "South Carolina"),
    ("SD", "South Dakota"), ("TN", "Tennessee"), ("TX", "Texas"), ("UT", "Utah"),
    ("VT", "Vermont"), ("VA", "Virginia"), ("WA", "Washington"), ("WV", "West Virginia"),
    ("WI", "Wisconsin"), ("WY", "Wyoming"), ("DC", "District of Columbia"),
]

# Channel icons for visual display in journey trees
CHANNEL_ICONS = {
    "MAIL": "[blue]📬[/blue]",
    "PHONE": "[green]📞[/green]",
    "PHONE_OUTBOUND": "[green]📞[/green]",
    "PHONE_INBOUND": "[cyan]📲[/cyan]",
    "EMAIL": "[yellow]📧[/yellow]",
    "SMS": "[magenta]💬[/magenta]",
    "AGENT_VISIT": "[red]🏠[/red]",
    "PORTAL": "[white]🌐[/white]",
}

# Node type icons for journey tree visualization
NODE_TYPE_ICONS = {
    "entry": "[green]▶[/green]",
    "touchpoint": "[cyan]●[/cyan]",
    "wait": "[yellow]⏳[/yellow]",
    "decision": "[magenta]◆[/magenta]",
    "status": "[blue]◉[/blue]",
    "exit": "[red]■[/red]",
}
