#!/usr/bin/env python3
"""
Demo script to showcase Google search and reminder functionality
"""

import agent
import time

def demo_google_search():
    """Demonstrate Google search functionality"""
    print("=" * 60)
    print("GOOGLE SEARCH FUNCTIONALITY DEMO")
    print("=" * 60)
    
    # Test various search queries
    search_examples = [
        "latest AI news",
        "python programming tutorials", 
        "machine learning basics",
        "what is artificial intelligence"
    ]
    
    for i, query in enumerate(search_examples, 1):
        print(f"\n{i}. Searching for: '{query}'")
        print("-" * 40)
        
        try:
            result = agent.search_web(query)
            # Truncate for display
            if len(result) > 300:
                result = result[:300] + "..."
            print(result)
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "="*60)

def demo_reminder_system():
    """Demonstrate reminder system functionality"""
    print("\n" + "=" * 60)
    print("REMINDER SYSTEM FUNCTIONALITY DEMO")
    print("=" * 60)
    
    # Test various reminder scenarios
    reminder_examples = [
        ("Call mom", "at 3 PM"),
        ("Buy groceries", "in 2 hours"),
        ("Team meeting", "tomorrow at 9 AM"),
        ("Take medicine", "in 30 minutes"),
        ("Dentist appointment", "next week"),
        ("Submit report", "at 5 PM today")
    ]
    
    print("\nSetting up reminders:")
    print("-" * 40)
    
    for i, (reminder_text, time_str) in enumerate(reminder_examples, 1):
        print(f"\n{i}. Setting reminder: '{reminder_text}' {time_str}")
        
        try:
            response = agent.set_reminder(reminder_text, time_str)
            print(f"   Response: {response}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "="*60)
    print("Checking for due reminders...")
    print("-" * 40)
    
    try:
        due_reminders = agent.get_due_reminders()
        if due_reminders:
            print("Due reminders found:")
            for reminder in due_reminders:
                print(f"• {reminder}")
        else:
            print("No reminders are due right now.")
    except Exception as e:
        print(f"Error checking reminders: {e}")

def demo_basic_commands():
    """Demonstrate basic assistant commands"""
    print("\n" + "=" * 60)
    print("BASIC ASSISTANT COMMANDS DEMO")
    print("=" * 60)
    
    basic_examples = [
        "Hello, how are you?",
        "What time is it?",
        "What's today's date?",
        "Calculate 15 * 8",
        "What is 100 divided by 4?"
    ]
    
    for i, command in enumerate(basic_examples, 1):
        print(f"\n{i}. Command: '{command}'")
        print("-" * 40)
        
        try:
            response = agent.process_command(command)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "="*60)

def main():
    """Run the complete demo"""
    print("PERSONAL ASSISTANT DEMO")
    print("Features: Google Search & Basic Reminders")
    print("=" * 60)
    
    # Demo basic commands first
    demo_basic_commands()
    
    # Demo Google search
    demo_google_search()
    
    # Demo reminder system
    demo_reminder_system()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETED!")
    print("=" * 60)
    print("\nTo use the web interface:")
    print("1. Run: python app.py")
    print("2. Open: http://localhost:5000")
    print("3. Try commands like:")
    print("   - 'Search for latest AI news'")
    print("   - 'Remind me to call mom at 3 PM'")
    print("   - 'What time is it?'")
    print("   - 'Calculate 25 * 4'")

if __name__ == "__main__":
    main()
