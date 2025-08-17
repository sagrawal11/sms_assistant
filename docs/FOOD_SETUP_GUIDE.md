# 🍽️ College Food Setup Guide

## **📋 How to Add Your College Dining Hall Foods**

### **1. Find Nutritional Information**
- Check your college's dining services website
- Look for nutrition facts or calorie counts
- Ask dining staff for nutritional information
- Use apps like MyFitnessPal for estimates

### **2. Add Foods to `wu_foods.json`**

#### **Basic Format:**
```json
"food_name": {
  "restaurant": "restaurant_name",
  "calories": 0,
  "protein": 0,
  "carbs": 0,
  "fat": 0,
  "fiber": 0,
  "serving_size": "description",
  "common_servings": ["serving1", "serving2", "serving3"]
}
```

#### **Example - Adding Scrambled Eggs:**
```json
"scrambled_eggs": {
  "restaurant": "main_dining",
  "calories": 140,
  "protein": 12,
  "carbs": 2,
  "fat": 10,
  "fiber": 0,
  "serving_size": "2 eggs",
  "common_servings": ["1 egg", "2 eggs", "3 eggs"]
}
```

### **3. Restaurant Names to Use**
- `main_dining` - Main dining hall
- `convenience_store` - Campus store/snack bar
- `chick_fil_a` - Chick-fil-A on campus
- `mcdonalds` - McDonald's on campus
- `starbucks` - Campus Starbucks
- `pizza_place` - Campus pizza place
- `subway` - Subway on campus

### **4. Common Food Categories**

#### **Breakfast:**
- Eggs (scrambled, fried, omelette)
- Oatmeal, cereal, granola
- Pancakes, waffles, French toast
- Bagels, toast, muffins
- Yogurt, fruit, smoothies

#### **Lunch/Dinner:**
- Grilled chicken, fish, beef
- Pasta, rice, potatoes
- Salads, vegetables
- Soups, sandwiches
- Pizza, burgers

### **5. Snacks Database**

#### **File**: `snacks.json` - Already populated with common snacks:
- **Protein bars**: Quest, Clif, Power Crunch
- **Nuts & seeds**: Almonds, peanuts, cashews, sunflower seeds
- **Fruits**: Apple, banana, orange, grapes
- **Chips & crackers**: Tortilla chips, pretzels, Goldfish
- **Dairy snacks**: String cheese, Greek yogurt, cottage cheese

#### **To add new snacks:**
```json
"new_snack": {
  "calories": 150,
  "protein": 5,
  "carbs": 20,
  "fat": 7,
  "fiber": 2,
  "serving_size": "1 serving",
  "common_servings": ["1/2 serving", "1 serving", "2 servings"]
}
```

### **6. How to Use in Alfred the Butler**

#### **Text these messages:**
- **"ate scrambled eggs for breakfast"** → Logs eggs with full macros
- **"had grilled chicken and brown rice for lunch"** → Logs both items
- **"snack: quest bar"** → Logs protein bar with macros
- **"dinner: salmon with broccoli"** → Logs both items

#### **Alfred will:**
1. ✅ **Recognize the food** from your databases
2. ✅ **Log the macros** automatically
3. ✅ **Track daily totals** (calories, protein, carbs, fat)
4. ✅ **Send push notification** with logged info

### **7. Pro Tips**

#### **Add Foods as You Go:**
- Don't try to add everything at once
- Add foods the day before you plan to eat them
- Start with your most common meals

#### **Be Specific:**
- Use exact names from the dining hall menu
- Include restaurant names for accuracy
- Add serving size variations you'll actually use

#### **Update Regularly:**
- Add new menu items as they change
- Update nutritional info if it changes
- Remove foods you don't eat anymore

### **8. Example Complete Entry**

```json
"grilled_chicken_breast": {
  "restaurant": "main_dining",
  "calories": 165,
  "protein": 31,
  "carbs": 0,
  "fat": 3.6,
  "fiber": 0,
  "serving_size": "4 oz cooked",
  "common_servings": ["3 oz", "4 oz", "6 oz", "8 oz"]
}
```

### **9. Need Help?**

- Look at existing entries in `wu_foods.json` for examples
- Check `snacks.json` for snack format examples
- Test with simple foods first before adding complex meals

---

**🎯 Goal: Build a database of 20-30 foods you'll eat regularly in college!**

**📁 Files to edit:**
- `wu_foods.json` - Your college dining hall foods
- `snacks.json` - Common snacks (already populated)
