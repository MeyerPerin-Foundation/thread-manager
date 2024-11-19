from datetime import datetime

def calculate_date_difference(fixed_date):
    """
    Calculate the difference in days between today and a fixed date.

    Args:
        fixed_date (str): The fixed date in 'YYYY-MM-DD' format.

    Returns:
        int: The difference in days (positive if today is later, negative if earlier).
    """
    try:
        # Convert the fixed date string to a datetime object
        fixed_date_obj = datetime.strptime(fixed_date, '%Y-%m-%d').date()
        
        # Get today's date
        today = datetime.today().date()
        
        # Calculate the difference in days
        difference = (today - fixed_date_obj).days
        
        return difference
    except ValueError:
        return "Invalid date format. Please use 'YYYY-MM-DD'."
    
    
def days_until_midterms() -> str:
    """
    Calculate the number of days until the next midterms.

    Returns:
        str: A message with the number of days until the next midterms.
    """
    # Fixed date for the next midterms
    midterms_date = '2026-11-03'
    
    # Calculate the difference in days
    difference = calculate_date_difference(midterms_date)
    
    if isinstance(difference, int):
        if difference > 0:
            return f"There are {difference} days until the next midterms."
        elif difference == 0:
            return "Midterms are today!"
        else:
            return f"There are {abs(difference)} days until the next midterms."
    else:
        return difference