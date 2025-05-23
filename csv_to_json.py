#!/usr/bin/env python3
import csv, json, sys, os, pandas as pd

def convert_csv_to_json(input_file: str, output_file: str, encoding: str = "latin-1"):
    print(f"Current working directory: {os.getcwd()}")
    print(f"Input file path: {os.path.abspath(input_file)}")
    print(f"Output file path: {os.path.abspath(output_file)}")
    
    try:
        print(f"Attempting to open input file: {input_file}")
        df = pd.read_csv(input_file, encoding=encoding)
        print("Successfully read CSV into pandas DataFrame.")
        print("\nColumns after reading CSV:")
        print(df.columns.tolist())
        print("Sample ISO3166-2 column after reading CSV:")
        if 'ISO3166-2' in df.columns:
            print(df['ISO3166-2'].head(10).to_list())
        else:
            print("ISO3166-2 column not found!")
        
        # Drop the first column and handle NA values
        df = df.iloc[:, 1:].copy()  # Create a copy to avoid SettingWithCopyWarning
        print("\nColumns after dropping first column:")
        print(df.columns.tolist())
        print("Sample ISO3166-2 column after dropping first column:")
        if 'ISO3166-2' in df.columns:
            print(df['ISO3166-2'].head(10).to_list())
        else:
            print("ISO3166-2 column not found!")
        
        # Fill NA values in ISO3166-2 column with empty string to avoid NaN issues
        if 'ISO3166-2' in df.columns:
            df['ISO3166-2'] = df['ISO3166-2'].fillna('')
            # Filter rows where ISO3166-2 starts with '1'
            df = df[df['ISO3166-2'].str.startswith('1', na=False)]
        else:
            print("ISO3166-2 column missing after dropping first column. Exiting.")
            sys.exit(1)
        
        print(f"Filtered DataFrame has {len(df)} rows.")
        print(f"Attempting to write output file: {output_file}")
        df.to_json(output_file, orient="records", indent=2, force_ascii=False)
        print("Successfully wrote JSON data (using pandas's to_json).")
        print(f"Output file size: {os.path.getsize(output_file)} bytes")
        
        # Print some sample rows for verification
        if len(df) > 0:
            print("\nSample of filtered data:")
            print(df[['Country', 'Name', 'ISO3166-2']].head().to_string())
    except FileNotFoundError as e:
        print(f"File not found error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        print(f"Error type: {type(e)}", file=sys.stderr)
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python csv_to_json.py input.csv output.json")
        sys.exit(1)
    convert_csv_to_json(sys.argv[1], sys.argv[2]) 