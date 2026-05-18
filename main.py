import os
from dotenv import load_dotenv
from brain.gemini import JarvisBrain
from brain.skill_router import SkillRouter
from brain.task_planner import TaskPlanner

# Main entry point for JARVIS
# Currently runs a text-based loop for testing the Brain, Router, and Planner

def main():
    # Load environment variables
    load_dotenv(override=True)
    
    print("Initializing JARVIS Systems...\n")
    
    # Initialize the core brain modules
    brain = JarvisBrain()
    router = SkillRouter()
    planner = TaskPlanner()
    
    print("\n[SYSTEM] All modules online. Waiting for input (type 'quit' to exit).")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ["quit", "exit", "stop"]:
                print("JARVIS: Goodbye, sir.")
                break
                
            if not user_input:
                continue
                
            # Step 1: Classify the intent
            category = router.route_intent(user_input)
            print(f"[SYSTEM] Intent classified as: {category.upper()}")
            
            # Step 2: If it's a complex task (not general conversation or simple web search), 
            # we might want to plan it. For now, we plan tasks that are clearly actions.
            if category in ["downloader", "pc_control", "files", "browser"]:
                plan = planner.plan_task(user_input)
                print(f"[SYSTEM] Generated Task Plan: {plan}")
                
                # We tell the brain about the plan so it can respond appropriately
                brain_context = f"The user asked to '{user_input}'. I have created this plan: {plan}. Inform the user that you are initiating this plan."
                reply = brain.think(brain_context)
            else:
                # Step 3: Normal conversation or direct skill handling
                reply = brain.think(user_input)
                
            print(f"\nJARVIS: {reply}")
            
        except KeyboardInterrupt:
            print("\nJARVIS: Goodbye, sir.")
            break
        except Exception as e:
            print(f"\n[SYSTEM] Critical Error: {e}")

if __name__ == "__main__":
    main()
