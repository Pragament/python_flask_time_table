import pandas as pd
import os
import argparse
import re

def process_timetable(df):
    """
    Process teacher timetable data specifically, handling the structure seen in the example.
    """
    # Extract teacher name and subject
    teacher_name = None
    subject = None
    
    for i in range(5):  # Check first few rows for headers
        if i < len(df):
            row = df.iloc[i]
            for col in df.columns:
                val = row.get(col, "")
                if pd.notna(val) and isinstance(val, str):
                    if "Name of the Teacher:" in val:
                        teacher_name = val.split("Name of the Teacher:")[1].strip()
                    elif "Subject :" in val:
                        subject = val.split("Subject :")[1].strip()
    
    # Find the start of the actual timetable (usually after "Timings" row)
    start_row = None
    for i, row in df.iterrows():
        if row.iloc[0] == "Timings" or (isinstance(row.iloc[0], str) and "Timings" in row.iloc[0]):
            start_row = i
            break
    
    if start_row is not None:
        # Extract days of the week
        days_row = df.iloc[start_row + 1]
        days = []
        for i in range(len(days_row)):
            if pd.notna(days_row.iloc[i]) and days_row.iloc[i] in ["Mon", "Tue", "Wed", "Thurs", "Fri", "Sat"]:
                days.append(days_row.iloc[i])
        
        # Create structured timetable data
        timetable_data = []
        
        # Extract periods/timings
        periods_row = df.iloc[start_row]
        periods = []
        for i in range(len(periods_row)):
            if pd.notna(periods_row.iloc[i]) and i > 0:  # Skip the first column which contains "Timings"
                periods.append(periods_row.iloc[i])
        
        # Extract timing information (usually in the first column)
        timings = []
        for i in range(start_row + 1, len(df)):
            if i < len(df) and pd.notna(df.iloc[i, 0]) and df.iloc[i, 0] in ["Mon", "Tue", "Wed", "Thurs", "Fri", "Sat"]:
                day = df.iloc[i, 0]
                day_data = {"Day": day}
                
                # Add periods for this day
                for j, period in enumerate(periods, 1):
                    if j < len(df.columns):
                        class_info = df.iloc[i, j]
                        if pd.notna(class_info):
                            day_data[f"Period_{j}"] = class_info
                        else:
                            day_data[f"Period_{j}"] = ""
                
                timetable_data.append(day_data)
        
        # Create a structured DataFrame for the timetable
        timetable_df = pd.DataFrame(timetable_data)
        
        return {
            "teacher_name": teacher_name,
            "subject": subject,
            "timetable": timetable_df
        }
    
    return {
        "teacher_name": teacher_name,
        "subject": subject,
        "timetable": None
    }

def extract_teachers_list(df):
    """Extract teachers list from a sheet with teacher names."""
    # Clean the dataframe
    df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    
    # Look for common headers in teacher lists
    common_headers = ["S.NO", "NAME OF THE TEACHER", "TEACHER NAME", "SL NO"]
    
    # Check if any common header is present
    header_row = None
    for i in range(min(10, len(df))):  # Check first 10 rows
        row = df.iloc[i]
        for header in common_headers:
            for col in df.columns:
                if pd.notna(row.get(col)) and isinstance(row.get(col), str) and header in row.get(col).upper():
                    header_row = i
                    break
            if header_row is not None:
                break
        if header_row is not None:
            break
    
    if header_row is not None:
        # Extract teachers list with proper headers
        teachers_df = df.iloc[header_row:].reset_index(drop=True)
        teachers_df.columns = teachers_df.iloc[0]
        teachers_df = teachers_df.iloc[1:].reset_index(drop=True)
        return teachers_df
    else:
        # Just return the cleaned dataframe
        return df

def is_timetable_sheet(df):
    """Check if the sheet is a timetable based on certain keywords."""
    # Convert the first few rows to a string and check for timetable indicators
    sample = str(df.iloc[0:10].values)
    return "TIME TABLE" in sample or "TIMETABLE" in sample

def is_teachers_list(df):
    """Check if the sheet contains a list of teachers."""
    sample = str(df.iloc[0:10].values)
    return "TEACHER" in sample and ("S.NO" in sample or "SL NO" in sample)

def convert_excel_to_csv(input_file, output_dir):
    """Convert Excel file to CSV, processing different types of sheets appropriately."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Get the base filename without extension
    base_name = os.path.basename(input_file).split('.')[0]
    
    # Read the Excel file
    excel_file = pd.ExcelFile(input_file)
    
    results = []
    
    # Process each sheet
    for sheet_name in excel_file.sheet_names:
        try:
            # Read the sheet
            df = pd.read_excel(input_file, sheet_name=sheet_name)
            
            # Skip empty sheets
            if df.empty or df.isna().all().all():
                print(f"Skipping empty sheet: {sheet_name}")
                continue
            
            # Clean the dataframe
            df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
            
            # Determine the type of sheet
            sheet_type = "unknown"
            processed_df = df
            
            if is_timetable_sheet(df):
                sheet_type = "timetable"
                timetable_data = process_timetable(df)
                
                if timetable_data["timetable"] is not None:
                    processed_df = timetable_data["timetable"]
                
                results.append({
                    "sheet": sheet_name,
                    "type": "timetable",
                    "teacher": timetable_data["teacher_name"],
                    "subject": timetable_data["subject"]
                })
                
            elif is_teachers_list(df):
                sheet_type = "teachers_list"
                processed_df = extract_teachers_list(df)
                results.append({
                    "sheet": sheet_name,
                    "type": "teachers_list",
                    "count": len(processed_df)
                })
            
            # Generate output CSV filename
            csv_filename = f"{base_name}_{sheet_name}_{sheet_type}.csv"
            output_path = os.path.join(output_dir, csv_filename)
            
            # Save to CSV
            processed_df.to_csv(output_path, index=False)
            print(f"Converted sheet '{sheet_name}' to {csv_filename} as {sheet_type}")
            
        except Exception as e:
            print(f"Error processing sheet '{sheet_name}': {str(e)}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Convert Excel files with teacher timetables to CSV format.')
    parser.add_argument('input_files', nargs='+', help='Input Excel files to convert')
    parser.add_argument('--output_dir', default='csv_output', help='Output directory for CSV files')
    
    args = parser.parse_args()
    
    all_results = []
    
    for input_file in args.input_files:
        if not os.path.exists(input_file):
            print(f"Error: File {input_file} does not exist.")
            continue
            
        print(f"\nProcessing: {input_file}")
        results = convert_excel_to_csv(input_file, args.output_dir)
        all_results.extend(results)
        
    print("\nSummary of processed sheets:")
    
    timetables = [r for r in all_results if r["type"] == "timetable"]
    if timetables:
        print("\nTimetables:")
        for tt in timetables:
            print(f"  Sheet: {tt['sheet']}, Teacher: {tt.get('teacher', 'Unknown')}, Subject: {tt.get('subject', 'Unknown')}")
    
    teacher_lists = [r for r in all_results if r["type"] == "teachers_list"]
    if teacher_lists:
        print("\nTeacher Lists:")
        for tl in teacher_lists:
            print(f"  Sheet: {tl['sheet']}, Teachers Count: {tl.get('count', 'Unknown')}")
    
    print(f"\nAll CSV files have been saved to: {os.path.abspath(args.output_dir)}")

if __name__ == "__main__":
    main()