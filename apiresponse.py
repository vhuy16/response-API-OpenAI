from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any
import json
import re

# Create the Pydantic class
class TravelPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destination: str
    duration: str
    number_of_people: int
    budget: str
    activities: List[str]
    accommodations: List[str]
    transportation: List[str]
    estimated_cost: str

class UserInfo:
    def __init__(self):
        self.name = None
        self.preferences = {}
        self.last_interaction = None
        self.travel_history = []

class AgentMemory:
    def __init__(self):
        self.conversation_history = []
        self.travel_plans_cache = {}
        self.user_info = UserInfo()

    def add_to_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        self.user_info.last_interaction = content

    def get_recent_history(self, n: int = 5):
        return self.conversation_history[-n:]

    def cache_travel_plan(self, key: str, data: Dict[str, Any]):
        self.travel_plans_cache[key] = data

    def get_cached_plan(self, key: str):
        return self.travel_plans_cache.get(key)

    def update_user_info(self, name: str = None):
        if name:
            self.user_info.name = name

class TravelAgent:
    def __init__(self):
        self.client = OpenAI()
        self.memory = AgentMemory()
        self.schema = TravelPlan.model_json_schema()
        
        self.tools = [
            {
                "type": "web_search_preview",
               
            }
        ]

    def extract_travel_info(self, text: str) -> Dict[str, Any]:
        """Trích xuất thông tin du lịch từ câu hỏi"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract travel information from the text. Return a JSON with fields: 'destination', 'duration', 'number_of_people', 'budget'"},
                    {"role": "user", "content": text}
                ]
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {}

    def analyze_user_input(self, text: str) -> Dict[str, Any]:
        """Phân tích input của người dùng"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Analyze the user input and return a JSON with fields: 'type' (planning/inquiry/general), 'intent' (what they want to know), 'sentiment' (positive/negative/neutral)"},
                    {"role": "user", "content": text}
                ]
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"type": "general", "intent": "unknown", "sentiment": "neutral"}

    def plan_response(self, user_input: str) -> str:
        """Lập kế hoạch phản hồi"""
        # Phân tích input
        analysis = self.analyze_user_input(user_input)
        travel_info = self.extract_travel_info(user_input)
        
        # Xử lý theo loại câu hỏi
        if analysis["type"] == "planning":
            if travel_info.get('destination'):
                travel_plan = self.get_travel_plan(travel_info)
                return self.create_travel_plan_response(travel_plan, analysis)
            return "Bạn muốn đi du lịch ở đâu vậy?"
        elif analysis["type"] == "inquiry":
            return self.create_inquiry_response(travel_info, analysis)
        else:
            return self.create_general_response(user_input, analysis)

    def get_travel_plan(self, travel_info: Dict[str, Any]) -> Dict[str, Any]:
        """Lấy thông tin kế hoạch du lịch"""
        cache_key = f"{travel_info.get('destination')}_{travel_info.get('duration')}_{travel_info.get('number_of_people')}"
        cached_plan = self.memory.get_cached_plan(cache_key)
        if cached_plan:
            return cached_plan
        
        try:
            input_messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"Tạo kế hoạch du lịch cho {travel_info.get('destination')} trong {travel_info.get('duration')} ngày cho {travel_info.get('number_of_people')} người với ngân sách {travel_info.get('budget')}"
                        },
                    ]
                }
            ]

            response = self.client.responses.create(
                model="gpt-4o-mini",
                instructions="Create a detailed travel plan using web search results. Include activities, accommodations, transportation, and cost estimates.",
                input=input_messages,
                tools=self.tools,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "travel_plan",
                        "schema": self.schema,
                        "strict": True
                    }
                }
            )

            travel_plan = json.loads(response.output_text)
            self.memory.cache_travel_plan(cache_key, travel_plan)
            return travel_plan
        except Exception as e:
            return None

    def create_travel_plan_response(self, travel_plan: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Tạo câu trả lời với kế hoạch du lịch"""
        if not travel_plan:
            return "Xin lỗi, tôi không thể tạo kế hoạch du lịch lúc này."

        destination = travel_plan.get('destination', '')
        duration = travel_plan.get('duration', '')
        number_of_people = travel_plan.get('number_of_people', 0)
        budget = travel_plan.get('budget', '')
        activities = travel_plan.get('activities', [])
        accommodations = travel_plan.get('accommodations', [])
        transportation = travel_plan.get('transportation', [])
        estimated_cost = travel_plan.get('estimated_cost', '')

        # Tạo câu trả lời
        response = f"Kế hoạch du lịch cho {destination}:\n\n"
        response += f"Thời gian: {duration}\n"
        response += f"Số người: {number_of_people}\n"
        response += f"Ngân sách: {budget}\n\n"
        
        response += "Các hoạt động đề xuất và giá:\n"
        for i, activity in enumerate(activities, 1):
            # Thêm giá cho mỗi hoạt động
            activity_price = self.get_activity_price(activity)
            response += f"{i}. {activity} - Giá: {activity_price}\n"
        
        response += "\nChỗ ở đề xuất và giá:\n"
        for i, accommodation in enumerate(accommodations, 1):
            # Thêm giá cho mỗi chỗ ở
            accommodation_price = self.get_accommodation_price(accommodation)
            response += f"{i}. {accommodation} - Giá: {accommodation_price}\n"
        
        response += "\nPhương tiện di chuyển và giá:\n"
        for i, transport in enumerate(transportation, 1):
            # Thêm giá cho mỗi phương tiện
            transport_price = self.get_transport_price(transport)
            response += f"{i}. {transport} - Giá: {transport_price}\n"
        
        response += f"\nChi phí ước tính tổng cộng: {estimated_cost}\n"
        
        # Thêm lời khuyên
        response += "\nLời khuyên:\n"
        response += "- Nên đặt vé và phòng trước để có giá tốt\n"
        response += "- Mang theo giấy tờ tùy thân và bảo hiểm du lịch\n"
        response += "- Kiểm tra thời tiết trước khi đi\n"
        response += "- Chuẩn bị sẵn bản đồ và thông tin liên hệ khẩn cấp\n"
        response += "- Có thể thương lượng giá với các nhà cung cấp dịch vụ"

        return response

    def get_activity_price(self, activity: str) -> str:
        """Lấy giá cho hoạt động"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Return the estimated price for the activity in VND format"},
                    {"role": "user", "content": f"What is the price for {activity}?"}
                ]
            )
            return response.choices[0].message.content
        except:
            return "Liên hệ để biết giá"

    def get_accommodation_price(self, accommodation: str) -> str:
        """Lấy giá cho chỗ ở"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Return the estimated price for the accommodation in VND format per night"},
                    {"role": "user", "content": f"What is the price for {accommodation}?"}
                ]
            )
            return response.choices[0].message.content
        except:
            return "Liên hệ để biết giá"

    def get_transport_price(self, transport: str) -> str:
        """Lấy giá cho phương tiện di chuyển"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Return the estimated price for the transportation in VND format"},
                    {"role": "user", "content": f"What is the price for {transport}?"}
                ]
            )
            return response.choices[0].message.content
        except:
            return "Liên hệ để biết giá"

    def create_inquiry_response(self, travel_info: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Tạo câu trả lời cho câu hỏi thông tin"""
        destination = travel_info.get('destination', '')
        if destination:
            return f"Tôi sẽ tìm kiếm thông tin về {destination} cho bạn. Bạn muốn biết thông tin gì cụ thể không? Ví dụ: địa điểm tham quan, khách sạn, nhà hàng, v.v."
        return "Bạn muốn tìm hiểu thông tin về địa điểm nào vậy?"

    def create_general_response(self, user_input: str, analysis: Dict[str, Any]) -> str:
        """Tạo câu trả lời chung"""
        return "Tôi có thể giúp bạn lên kế hoạch du lịch. Bạn muốn đi đâu, trong bao lâu và với ngân sách bao nhiêu?"

    def process_user_input(self, user_input: str) -> str:
        """Xử lý input của người dùng"""
        self.memory.add_to_history("user", user_input)
        response = self.plan_response(user_input)
        self.memory.add_to_history("assistant", response)
        return response

def main():
    agent = TravelAgent()
    print("Xin chào! Tôi là AI Agent lên kế hoạch du lịch. Tôi có thể:")
    print("1. Lên kế hoạch du lịch chi tiết")
    print("2. Tìm kiếm thông tin về địa điểm")
    print("3. Đề xuất các hoạt động và chỗ ở")
    print("4. Tính toán chi phí ước tính")
    print("\nVí dụ:")
    print("- 'Tôi muốn đi du lịch Đà Lạt 3 ngày 2 đêm cho 2 người với ngân sách 5 triệu'")
    print("- 'Có gì thú vị ở Phú Quốc không?'")
    print("- 'Kế hoạch du lịch Hạ Long 4 ngày 3 đêm cho gia đình 4 người'")
    print("\nGõ 'thoát' để kết thúc.")
    
    while True:
        user_input = input("\nBạn: ")
        
        if user_input.lower() == 'thoát':
            print("Tạm biệt! Chúc bạn có những chuyến du lịch thú vị!")
            break
            
        response = agent.process_user_input(user_input)
        print("\nAI:", response)

if __name__ == "__main__":
    main()