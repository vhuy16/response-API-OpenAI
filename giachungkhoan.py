from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

client = OpenAI()

class StockAnalysis:
    def __init__(self):
        self.tools = [
            {
                "type": "web_search_preview",
                # "description": "Tìm kiếm thông tin mới nhất về chứng khoán và tài chính từ cafef.vn",
                # "url": "https://cafef.vn/du-lieu/lich-su-giao-dich-vnm-1.chn"
            }
        ]

    def analyze_stock(self, question: str) -> str:
        try:
            # Thêm URL vào câu hỏi để tìm kiếm trên cafef.vn
            search_query = f"{question} site:cafef.vn/du-lieu/lich-su-giao-dich-vnm-1.chn"
            
            response = client.responses.create(
                model="gpt-4o",
                tools=self.tools,
                input=search_query,
                instructions="""Bạn là chuyên gia phân tích chứng khoán. Hãy phân tích và trả lời câu hỏi của người dùng dựa trên thông tin từ trang site:cafef.vn.
                Nếu câu hỏi liên quan đến:
                - Dòng tiền: Phân tích dựa trên báo cáo tài chính
                - Giao dịch: Sử dụng dữ liệu từ bảng lịch sử giao dịch
                - Định giá: So sánh với các chỉ số P/E, P/B của ngành
                - Rủi ro: Đánh giá dựa trên biến động giá và khối lượng
                Nếu không có đủ thông tin, hãy nêu rõ điều đó."""
            )
            return response.output_text
        except Exception as e:
            return f"Xin lỗi, có lỗi xảy ra: {str(e)}"

def main():
    print("Xin chào! Tôi là chatbot phân tích chứng khoán VNM. Tôi có thể giúp bạn phân tích:")
    print("1. Dòng tiền và khả năng chi trả cổ tức")
    print("2. Định giá cổ phiếu so với ngành")
    print("3. Thông tin giao dịch và thanh khoản")
    print("4. Phân tích kỹ thuật (MA, RSI, MACD)")
    print("5. Đánh giá rủi ro và tiềm năng tăng giá")
    print("\nVí dụ câu hỏi:")
    print("- 'Dòng tiền từ hoạt động kinh doanh có ổn định không?'")
    print("- 'Giá cổ phiếu có được định giá cao/thấp hơn so với ngành?'")
    print("- 'Giá trị giao dịch khớp lệnh trung bình hàng ngày là bao nhiêu?'")
    print("- 'Mức độ rủi ro của cổ phiếu này như thế nào?'")
    print("\nGõ 'thoát' để kết thúc.")

    analyzer = StockAnalysis()
    
    while True:
        user_input = input("\nBạn: ")
        
        if user_input.lower() == 'thoát':
            print("Tạm biệt! Cảm ơn bạn đã sử dụng dịch vụ phân tích chứng khoán!")
            break
            
        response = analyzer.analyze_stock(user_input)
        print("\nAI:", response)

if __name__ == "__main__":
    main()
