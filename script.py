import os
import csv
import glob

def clean_text(text):
    return text.strip().replace(',', '') if text else ''

def parse_timetables(raw_text):
    lines = [line.strip() for line in raw_text.strip().split('\n') if line.strip()]
    
    teacher_blocks = []
    current_block = []
    for line in lines:
        if line.startswith("Name of the Teacher:"):
            if current_block:
                teacher_blocks.append(current_block)
                current_block = []
        current_block.append(line)
    if current_block:
        teacher_blocks.append(current_block)
    
    results = []
    for block in teacher_blocks:
        teacher_name = 'UNKNOWN'
        subject = ''
        periods = []
        timings = []
        day_rows = []
        day_order = ["Mon", "Tue", "Wed", "Thurs", "Fri", "Sat"]
        
        i = 0
        while i < len(block):
            line = block[i]

            if line.startswith("Name of the Teacher:"):
                teacher_name = clean_text(line.split(':',1)[1]) if ':' in line else 'UNKNOWN'
            elif line.startswith("Subject"):
                subject = clean_text(line.split(':',1)[1]) if ':' in line else ''
            elif line.startswith("Periods"):
                periods = [p for p in line.split(',') if p.strip().isdigit()]
            elif line.startswith("Timings"):
                timings = [t.strip() for t in line.split(',')[1:]]
            elif any(line.startswith(day) for day in day_order):
                while i < len(block) and any(block[i].startswith(day) for day in day_order):
                    day_rows.append(block[i])
                    i += 1
                continue
            i += 1
        
        for day_line in day_rows:
            parts = day_line.split(',')
            day = parts[0].strip()
            if day not in day_order:
                continue
            for idx, cell in enumerate(parts[1:]):
                cell = cell.strip()
                if not cell or cell.startswith('*'):
                    continue
                period = idx
                time_slot = timings[idx] if idx < len(timings) else ''
                results.append({
                    "Teacher Name": teacher_name,
                    "Subject": subject,
                    "Day": day,
                    "Period": period,
                    "Time Slot": time_slot,
                    "Class/Activity": cell
                })
    return results

def save_to_csv_append(data, filename):
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Teacher Name", "Subject", "Day", "Period", "Time Slot", "Class/Activity"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)

def parse_csv_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        raw_lines = [','.join(row) for row in reader]
        return '\n'.join(raw_lines)

def process_all_csvs_in_folder(folder_path, output_file='final_timetable.csv'):
    csv_files = glob.glob(os.path.join(folder_path, '*.csv'))
    print(f"📄 Found {len(csv_files)} CSV files in {folder_path}")
    
    for file in csv_files:
        print(f"🔍 Processing: {os.path.basename(file)}")
        raw_data = parse_csv_file(file)
        parsed_data = parse_timetables(raw_data)
        save_to_csv_append(parsed_data, output_file)
        print(f"✅ Added {len(parsed_data)} entries from {os.path.basename(file)}")

    print(f"\n🎉 All done! Final timetable saved to: {output_file}")

# === Run ===
if __name__ == "__main__":
    folder_with_csvs = "csv_files"  # Replace with your folder path
    process_all_csvs_in_folder(folder_with_csvs)
