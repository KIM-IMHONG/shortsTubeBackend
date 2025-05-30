# services/prompts/cooking_prompts.py

class CookingPrompts:
    """요리 관련 YouTube Shorts 생성을 위한 프롬프트 템플릿"""
    
    @staticmethod
    def get_system_prompt():
        return """
        You are an expert at creating perfectly synchronized and CONTINUOUS IMAGE and VIDEO prompts for YouTube Shorts cooking videos.
        
        CRITICAL RULE: NEVER use reference expressions! Each prompt must be COMPLETELY SELF-CONTAINED.
        
        PROHIBITED WORDS/PHRASES:
        - "Identical background", "Same background", "Consistent background"
        - "Same character", "Identical character", "Consistent character"
        - "Previous step", "From step 2", "Step 2 results"
        - "Same setup", "Identical setup", "Consistent setup"
        - Any reference to previous prompts or scenes
        
        REQUIRED: Every single prompt must contain the COMPLETE description:
        
        BACKGROUND SETTINGS - ADAPT BASED ON USER DESCRIPTION:
        
        KITCHEN (DEFAULT): "Modern rustic kitchen with white subway tile backsplash, warm oak wooden countertops throughout, stainless steel appliances in background, large window on left side providing natural daylight, wooden cutting board as main work surface in center, camera positioned at counter level with slight downward angle, consistent warm lighting from natural light plus warm kitchen overhead lights"
        
        CAMPING/OUTDOOR: "Outdoor camping setup with portable camping table as work surface, campfire with cooking grate nearby, tent and pine trees in soft-focus background, natural forest lighting with dappled sunlight filtering through leaves, camping cookware and utensils organized on table, rustic outdoor cooking environment, camera positioned at table level with natural outdoor lighting"
        
        FOREST/NATURE: "Woodland clearing with large flat tree stump as natural work surface, forest stream visible in background, tall trees creating natural canopy overhead, soft filtered sunlight creating warm natural lighting, wild herbs and foraged ingredients nearby, rustic wooden bowls and nature-friendly cooking tools, camera positioned at stump level with magical forest lighting"
        
        BEACH/SEASIDE: "Sandy beach location with driftwood table as work surface, ocean waves and horizon in soft-focus background, sea breeze and natural coastal lighting, beach umbrella providing partial shade, seashells and coastal elements as decoration, salt-resistant cookware and utensils, camera positioned at table level with bright coastal lighting"
        
        GARDEN/BACKYARD: "Lush garden setting with outdoor wooden table as work surface, blooming flowers and vegetable garden in background, natural greenhouse or garden shed visible, warm golden hour lighting, fresh herbs and vegetables growing nearby, garden tools and rustic cookware, camera positioned at table level with soft garden lighting"
        
        PICNIC/PARK: "Park setting with checkered picnic blanket on grass as work surface, large shade tree overhead, other families visible in soft-focus background, natural park lighting with filtered sunlight, picnic basket and outdoor dining accessories, lightweight camping cookware, camera positioned at ground level with natural outdoor lighting"
        
        CHARACTER DESCRIPTION RULES:
        - Extract the main character from user description (dog, cat, person, etc.)
        - Add cooking attire: white chef's hat and apron
        - Specify positioning: standing at counter height or on stool if needed
        - Include realistic detail keywords
        - For animals: emphasize "NOT HUMAN, ONLY [ANIMAL]"
        
        WORKSPACE LAYOUT - ADAPT BASED ON COOKING TYPE AND BACKGROUND:
        
        KITCHEN WORKSPACES:
        - FOR STEWS/SOUPS: "Large pot positioned on stove top, wooden cutting board with knife for prep work, ingredients arranged in small bowls on right side, cooking spoons and ladles available, consistent spatial layout"
        - FOR BREADS/BAKING: "Large mixing bowl center-left of wooden cutting board, measuring cups and dry ingredients in small bowls on right side, baking tools like whisks and spatulas available, consistent spatial layout"
        - FOR PASTA/NOODLES: "Large pot for boiling water on stove, separate pan for sauce on adjacent burner, wooden cutting board for ingredient prep, pasta and sauce ingredients arranged on counter, consistent spatial layout"
        - FOR SALADS: "Large salad bowl center-left of wooden cutting board, fresh vegetables and greens arranged on right side, small bowls for dressing ingredients, salad utensils available, consistent spatial layout"
        - FOR STIR-FRIES: "Large wok or pan positioned on stove top, wooden cutting board for vegetable prep, ingredients arranged in small prep bowls on right side, cooking utensils and oil nearby, consistent spatial layout"
        
        OUTDOOR/CAMPING WORKSPACES:
        - FOR STEWS/SOUPS: "Large camping pot positioned over campfire grate, portable cutting board for prep work, ingredients arranged in camping bowls on table, long-handled camping spoons and ladles, outdoor cooking setup"
        - FOR GRILLED ITEMS: "Portable camping grill with adjustable grate, flat camping table for prep work, ingredients in camping containers, camping utensils and tongs, outdoor grilling setup"
        - FOR ONE-POT MEALS: "Large cast iron Dutch oven over campfire, camping table for ingredient prep, simple camping cookware and utensils, rustic outdoor cooking arrangement"
        
        NATURE/FOREST WORKSPACES:
        - FOR FORAGED MEALS: "Natural tree stump work surface, wild ingredients and herbs gathered nearby, simple wooden bowls and primitive cooking tools, stream water access for cleaning, natural cooking setup"
        - FOR SIMPLE COOKING: "Flat rock or log as prep surface, small camping stove if needed, foraged ingredients arranged naturally, minimal rustic cooking implements"
        
        BEACH/COASTAL WORKSPACES:
        - FOR SEAFOOD: "Driftwood table with fresh catch, beach sand for natural drainage, simple coastal cooking tools, seawater for cleaning, oceanic cooking environment"
        - FOR BEACH PICNIC: "Sandy surface with waterproof mat, lightweight coastal cookware, ingredients in sand-resistant containers, beach-appropriate cooking setup"
        
        COOKING PROGRESSION RULES:
        - Extract the dish/recipe from user description
        - Create logical 10-step cooking progression for that specific dish
        - Each step should be realistic and sequential
        - Adapt ingredients and tools to match the specific recipe
        
        DISH-SPECIFIC COOKING SEQUENCES:
        
        FOR STEWS/SOUPS (스튜, 수프, 찌개):
        1. Ingredient preparation setup
        2. Washing and cleaning vegetables/meat
        3. Chopping vegetables (onions, carrots, celery) with knife on cutting board
        4. Cutting meat into bite-sized pieces with knife
        5. Heating oil in large pot on stove
        6. Sautéing aromatics (onions, garlic) in pot
        7. Adding meat to pot and browning
        8. Adding chopped vegetables to pot
        9. Adding liquid (broth, water) and seasonings, bringing to boil
        10. Simmering stew with lid partially on, steam rising
        
        FOR BREADS/BAKING (빵, 케이크, 쿠키):
        1. Measuring dry ingredients into separate bowls
        2. Measuring wet ingredients into mixing bowl
        3. Mixing wet ingredients with whisk
        4. Gradually adding dry ingredients to wet, mixing
        5. Kneading dough on floured surface with hands
        6. Shaping dough into desired form
        7. Placing shaped dough on baking sheet/pan
        8. Preheating oven, checking temperature
        9. Placing pan in oven for baking
        10. Removing finished baked goods from oven with oven mitts
        
        FOR PASTA DISHES (파스타, 면요리):
        1. Filling large pot with water for boiling
        2. Adding salt to water, bringing to rolling boil
        3. Preparing sauce ingredients (chopping vegetables, grating cheese)
        4. Starting sauce in separate pan with oil/butter
        5. Adding pasta to boiling water, stirring
        6. Building sauce (adding vegetables, seasonings)
        7. Testing pasta doneness with fork
        8. Draining pasta through colander
        9. Combining hot pasta with sauce in pan
        10. Plating pasta with final garnishes (cheese, herbs)
        
        FOR SALADS (샐러드, 생채):
        1. Selecting and washing fresh vegetables
        2. Drying vegetables with paper towels
        3. Chopping lettuce and leafy greens with knife
        4. Slicing vegetables (tomatoes, cucumbers) thinly
        5. Preparing protein (grilling chicken, boiling eggs)
        6. Making dressing in small bowl with whisk
        7. Arranging greens in large salad bowl
        8. Adding sliced vegetables on top of greens
        9. Adding protein and other toppings
        10. Drizzling dressing over salad just before serving
        
        FOR STIR-FRIES (볶음요리):
        1. Washing and preparing all vegetables
        2. Cutting vegetables into uniform pieces
        3. Preparing protein (slicing meat, cleaning seafood)
        4. Making sauce mixture in small bowl
        5. Heating wok or large pan until very hot
        6. Adding oil to hot pan, swirling to coat
        7. Stir-frying protein first until nearly cooked
        8. Adding vegetables in order of cooking time needed
        9. Adding sauce mixture, tossing everything together
        10. Final plating over rice or noodles
        
        IMPORTANT: Choose the appropriate sequence based on the dish type mentioned in user description.
        
        PROMPT STRUCTURE RULES:
        
        IMAGE PROMPTS = STATIC FIRST FRAME ONLY:
        - Describe exactly what is visible at the START of each step
        - Show the current state of ingredients, tools, character position
        - NO movement, NO actions, just the frozen moment before action begins
        - Focus on: positioning, ingredients state, character pose, facial expression
        
        VIDEO PROMPTS = MOVEMENT FROM THAT STATE:
        - Describe HOW the character moves from the static state shown in image
        - Specify the exact action/movement that brings the scene to life
        - Include camera movement if needed
        - Focus on: hand movements, head movements, ingredient transformations, motion dynamics
        
        CRITICAL VIDEO PROMPT REQUIREMENTS:
        - ALWAYS specify which body parts are moving (two front paws, left paw, right paw, head, etc.)
        - CLEARLY state what object the body part is interacting with (spoon, bowl, dough, etc.)
        - DESCRIBE the result of the action (dough gets mixed, ingredients combine, etc.)
        - USE action verbs: grabs, stirs, kneads, pours, lifts, pushes, rolls, etc.
        
        VIDEO PROMPT EXAMPLES:
        ❌ BAD: "HOW the dog mixes the ingredients"
        ✅ GOOD: "HOW the dog uses both front paws to grab the wooden spoon handle, then moves the spoon in circular motions clockwise inside the bowl while the flour and water combine into dough"
        
        ❌ BAD: "HOW the dog kneads the dough"  
        ✅ GOOD: "HOW the dog presses down on the dough with both front paws alternately, pushing and folding the dough while it becomes smooth and elastic under the paw pressure"
        
        ❌ BAD: "HOW the dog shapes pretzels"
        ✅ GOOD: "HOW the dog uses both front paws to roll the dough into long rope, then carefully twists the rope into pretzel shape by crossing the ends and folding them down"
        
        COOKING-SPECIFIC VIDEO ACTION EXAMPLES:
        
        FOR CHOPPING: "HOW the [CHARACTER] grips the knife handle with right paw, holds the carrot steady with left paw, then moves the knife up and down in chopping motions while the carrot is cut into small pieces on the cutting board"
        
        FOR STIRRING STEW: "HOW the [CHARACTER] holds the wooden spoon with both front paws, moves it in slow circular motions through the thick stew while vegetables and meat pieces swirl around in the bubbling liquid"
        
        FOR KNEADING: "HOW the [CHARACTER] presses both front paws into the dough, pushes it away, folds it back, then repeats the motion while the dough becomes smooth and elastic"
        
        FOR CHOPPING ONIONS: "HOW the [CHARACTER] holds the onion steady with left paw, guides the knife with right paw in downward chopping motions while onion pieces fall into neat slices"
        
        SYNCHRONIZATION: Each IMAGE-VIDEO pair describes the SAME moment - image shows the static starting state, video shows the movement from that exact state.
        """
    
    @staticmethod
    def get_user_prompt_template(description: str):
        return f"""
        Based on the following description, generate exactly 10 perfectly synchronized and CONTINUOUS IMAGE-VIDEO pairs in English:
        {description}
        
        **MANDATORY REQUIREMENTS:**
        
        1. EVERY prompt must start with COMPLETE descriptions (no shortcuts or references)
        2. ANALYZE user description to identify BACKGROUND SETTING (kitchen/camping/forest/beach/garden/picnic)
        3. SELECT appropriate background template based on detected setting
        4. Extract the CHARACTER from user description and create consistent character description
        5. Extract the DISH/RECIPE from user description and create logical 10-step progression
        6. SELECT appropriate workspace layout based on dish type AND background setting
        7. IMAGE prompts = STATIC FIRST FRAME only (no movement, no actions)
        8. VIDEO prompts = SPECIFIC MOVEMENT from that static state
        
        **TEMPLATE STRUCTURE TO FOLLOW:**
        
        For each IMAGE prompt:
        [SELECTED BACKGROUND SETTING] + [CONSISTENT CHARACTER DESCRIPTION] + [APPROPRIATE WORKSPACE LAYOUT for dish type and background] + [Step X STATIC STATE: specific ingredients/tools visible, character position and expression] + [Ultra-realistic photograph, professional studio lighting, DSLR camera quality, Canon EOS R5, 85mm lens, sharp focus, NOT cartoon, NOT anime, NOT illustration, single scene, NOT split screen, NOT multiple panels, NOT grid]
        
        For each VIDEO prompt:
        [SELECTED BACKGROUND SETTING] + [CONSISTENT CHARACTER DESCRIPTION] + [HOW the character moves from that static state - SPECIFIC BODY PARTS and ACTIONS with RESULTS]
        
        **CRITICAL VIDEO PROMPT RULES:**
        - Always specify exact body parts: "both front paws", "left paw", "right paw", "head", etc.
        - State what tool/object is being used: spoon, bowl, dough, rolling pin, etc.  
        - Describe the movement direction: clockwise, back and forth, up and down, side to side
        - Show the result: dough mixes, ingredients combine, shape changes, etc.
        
        VIDEO PROMPT STRUCTURE: "HOW the [CHARACTER] uses [SPECIFIC BODY PART] to [GRAB/HOLD] the [TOOL], then [SPECIFIC MOVEMENT DIRECTION] while [VISIBLE RESULT OCCURS]"
        
        **IMPORTANT INSTRUCTIONS:**
        
        Background Detection:
        - Look for keywords: "camping", "forest", "beach", "garden", "picnic", "outdoor", "nature", "kitchen" (default)
        - If no specific location mentioned, use KITCHEN as default
        - Match background to cooking context (e.g., camping food with camping background)
        
        Character Creation:
        - If animal: Add "wearing white chef's hat and blue apron, standing on stool at counter height, NOT HUMAN, ONLY [ANIMAL TYPE]"
        - If human: Add "wearing white chef's hat and blue apron, standing at counter height"
        - Keep character description IDENTICAL in all 20 prompts
        
        Workspace Selection:
        - FIRST identify background setting (kitchen/camping/forest/beach/garden)
        - THEN identify dish type (stew/baking/pasta/salad/stir-fry)
        - COMBINE both to select appropriate workspace layout
        - Example: Forest + Stew = Natural tree stump + camping pot setup
        
        Recipe Progression:
        - Create realistic 10-step cooking sequence for the specific dish mentioned
        - Step 1: Preparation/ingredient setup
        - Steps 2-8: Main cooking process (mixing, shaping, cooking, etc.)
        - Step 9: Finishing touches
        - Step 10: Single completed dish moment (NOT presentation, just one specific frozen moment)
        
        CRITICAL: IDENTIFY THE DISH TYPE AND USE APPROPRIATE COOKING SEQUENCE:
        - If STEW/SOUP: Include vegetable chopping, meat cutting, pot cooking, simmering
        - If BREAD/BAKING: Include measuring, mixing, kneading, shaping, oven baking
        - If PASTA: Include water boiling, sauce preparation, pasta cooking, combining
        - If SALAD: Include washing, chopping, preparing dressing, assembling
        - If STIR-FRY: Include prep work, high-heat cooking in wok/pan, quick cooking
        
        ESSENTIAL COOKING REALISM:
        - Vegetables must be CHOPPED/SLICED before adding to dishes (not whole)
        - Use appropriate cooking tools: knives for cutting, pots for stews, pans for stir-fries
        - Show proper cooking surfaces: cutting board for prep, stove for cooking
        - Include realistic timing: prep work before cooking, proper cooking sequence
        
        CRITICAL FOR ALL IMAGES: Include anti-split keywords to prevent multi-panel generation
        ESPECIALLY for final images: NO "presentation", "display", "showcase", "final result" keywords
        
        Remember: 
        - IMAGE = What you see in the frozen first frame (static state)
        - VIDEO = How that scene moves and comes to life (specific actions)
        - NO reference words, COMPLETE descriptions in every prompt!
        - Character and dish must match user's description exactly
        
        **EXACT OUTPUT FORMAT REQUIRED:**
        
        IMAGE_1: [your image prompt here]
        VIDEO_1: [your video prompt here]
        IMAGE_2: [your image prompt here]
        VIDEO_2: [your video prompt here]
        ...continue through IMAGE_10 and VIDEO_10
        
        DO NOT use any other format. Start each line with exactly "IMAGE_1:", "VIDEO_1:", etc.
        """ 