from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

client = OpenAI()

class Order:
    def __init__(self):
        self.items = []
        self.total = 0
        self.special_requests = ""

    def add_item(self, name: str, price: float, quantity: int = 1):
        self.items.append({
            "name": name,
            "price": price,
            "quantity": quantity
        })
        self.total += price * quantity

    def add_special_request(self, request: str):
        self.special_requests = request

class ConversationHistory:
    def __init__(self):
        self.messages = []
        self.max_history = 5  # Lưu 5 câu hỏi gần nhất

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_history * 2:  # Mỗi cặp Q&A là 2 messages
            self.messages = self.messages[-self.max_history * 2:]

    def get_messages(self):
        return self.messages

def get_menu_response(user_input: str, current_order: Order = None, history: ConversationHistory = None) -> str:
    # Tạo input messages với lịch sử
    input_messages = []
    if history:
        input_messages.extend(history.get_messages())
    input_messages.append({
        "role": "user",
        "content": user_input
    })

    tools = [
        {
            "type": "file_search",
            "vector_store_ids": ["vs_67eb86b4070881919f5fd74d2b39b844"],
            "max_num_results": 2
        }
    ]

    response = client.responses.create(
        model="gpt-4o-mini",
        instructions="Bạn là nhân viên phục vụ trà sữa. Hãy trả lời câu hỏi của khách hàng dựa trên menu trà sữa và lịch sử câu hỏi trước đó. Nếu khách hàng hỏi về giá, hãy nêu rõ giá. Nếu hỏi về mô tả, hãy mô tả chi tiết món trà sữa đó. Nếu khách hàng muốn đặt món, hãy hướng dẫn họ cách đặt.",
        input=input_messages,
        tools=tools,
        include=["file_search_call.results"]
    )

    # Xử lý kết quả tìm kiếm
    menu_info = ""
    for output_item in response.output:
        if output_item.type == "file_search_call":
            for result in output_item.results:
                menu_info = result.text  # Chỉ lấy kết quả đầu tiên
                break
            break

    # Tạo câu trả lời dựa trên thông tin menu
    final_response = response.output_text

    # Xử lý đặt món
    if "đặt món" in user_input.lower() or "order" in user_input.lower():
        if current_order and current_order.items:
            final_response += "\n\nĐơn hàng hiện tại của bạn:\n"
            for item in current_order.items:
                final_response += f"- {item['name']} x{item['quantity']}: {item['price']*item['quantity']:,}đ\n"
            final_response += f"Tổng cộng: {current_order.total:,}đ\n"
            if current_order.special_requests:
                final_response += f"Yêu cầu đặc biệt: {current_order.special_requests}\n"
            final_response += "\nBạn có muốn xác nhận đơn hàng không? (có/không)"

    return final_response

def process_order(user_input: str, current_order: Order) -> tuple[str, Order]:
    if "xác nhận" in user_input.lower() and "có" in user_input.lower():
        if not current_order.items:
            return "Bạn chưa đặt món gì cả. Vui lòng đặt món trước khi xác nhận.", current_order
        
        # Xử lý đơn hàng thành công
        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        response = f"Đơn hàng của bạn đã được xác nhận!\n"
        response += f"Mã đơn hàng: {order_id}\n"
        response += f"Tổng tiền: {current_order.total:,}đ\n"
        response += "Cảm ơn bạn đã đặt hàng!"
        
        # Reset đơn hàng
        current_order = Order()
        return response, current_order
    
    elif "hủy" in user_input.lower():
        current_order = Order()
        return "Đơn hàng đã được hủy. Bạn có thể đặt món mới.", current_order
    
    return "Bạn có muốn xác nhận đơn hàng không? (có/không)", current_order

def main():
    print("Xin chào! Tôi là nhân viên phục vụ trà sữa. Tôi có thể giúp gì cho bạn?")
    print("Ví dụ:")
    print("- 'Cho tôi xem menu trà sữa'")
    print("- 'Trà sữa trân châu giá bao nhiêu?'")
    print("- 'Mô tả trà sữa matcha'")
    print("- 'Có những loại topping nào?'")
    print("- 'Tôi muốn đặt món'")
    print("\nGõ 'thoát' để kết thúc.")
    print("Gõ 'hủy' để hủy đơn hàng hiện tại.")
    print("Gõ 'xóa lịch sử' để xóa lịch sử câu hỏi.")

    current_order = Order()
    history = ConversationHistory()
    
    while True:
        user_input = input("\nBạn: ")
        
        if user_input.lower() == 'thoát':
            print("Tạm biệt! Cảm ơn bạn đã ghé thăm!")
            break
            
        if user_input.lower() == 'xóa lịch sử':
            history = ConversationHistory()
            print("Đã xóa lịch sử câu hỏi!")
            continue
            
        # Lưu câu hỏi của người dùng
        history.add_message("user", user_input)
        
        # Lấy câu trả lời
        response = get_menu_response(user_input, current_order, history)
        print("\nAI:", response)
        
        # Lưu câu trả lời của AI
        history.add_message("assistant", response)
        
        # Xử lý đặt món
        if current_order.items:
            response, current_order = process_order(user_input, current_order)
            print("\nAI:", response)
            history.add_message("assistant", response)

if __name__ == "__main__":
    main()


for output_item in response.output:

    if output_item.type == "file_search_call":
        print("Search Results:")
        for i, result in enumerate(output_item.results, 1):
            print(f"Results {i}")
            print(f"Filename: {result.filename}")
            print(f"Score: {result.score}")
            print(f"Text snippet: {result.text[:150]}..." if len(result.text) > 150 else f"Text snippet: {result.text}" )

    if output_item.type == "message":
        for content_item in output_item.content:
            if content_item.type == "output_text":
                print("Annotation: ")
                for annotation in content_item.annotations:
                    if annotation.type == "file_citation":
                        print(f"- Citation from File: {annotation.filename}")
