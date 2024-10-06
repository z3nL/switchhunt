import matplotlib.pyplot as plt
import openai

async def create_pie(dataframe, identifier, exclude_categories=None, output_file="pie_chart.png"):
    # Group by transaction type and sum the amounts
    pie_data = dataframe.groupby(identifier)['amount'].sum()

    # Exclude specified categories if provided
    if exclude_categories:
        pie_data = pie_data[~pie_data.index.isin(exclude_categories)]

    # Check if there's any data left to plot
    if pie_data.empty:
        print("No data available to display.")
        return

    # Create a pie chart
    plt.figure(figsize=(8, 6))
    # Set font properties
    font_properties = {'weight': 'bold', 'size': 12}  # Bold font

    # Create the pie chart without percentages
    plt.pie(pie_data, labels=pie_data.index, labeldistance=1.1, startangle=140, textprops=font_properties)
    plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular

    # Save the pie chart as a PNG file
    plt.savefig(output_file, format='png', bbox_inches='tight')
    
# Use ChatGPT to extract the company name out of a transaction description
async def extractCo(description, openai):
    completion = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are tasked with extracting the name of a company or organization"
                    " from a bank transaction description. Ignore irrelevant words or codes"
                    " such as 'TST*', 'POS', location names, or other non-company identifiers."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Given the bank transaction description: '{description}', "
                    "please return only the company/organization name involved."
                    "do NOT return a complete sentence. ONLY return a name."
                )
            }
        ]
    )
    response = completion['choices'][0]['message']['content'].strip()
    return response