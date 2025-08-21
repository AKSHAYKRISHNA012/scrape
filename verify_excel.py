"""
Excel File Verification Script
=============================
Quick script to display the contents of the generated Excel file
and verify all requirements are met.
"""

import pandas as pd
import os

def verify_excel_file(filename="TechCompany_Jobs.xlsx"):
    """
    Verify the generated Excel file meets all requirements.
    """
    
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found!")
        return False
    
    try:
        # Read the Excel file
        df = pd.read_excel(filename)
        
        print("=" * 60)
        print(f"EXCEL FILE VERIFICATION: {filename}")
        print("=" * 60)
        
        # Check required columns
        required_columns = [
            'JobTitle', 'Location', 'ExperienceRequired', 
            'SkillsRequired', 'Salary', 'JobURL', 'JobDescriptionSummary'
        ]
        
        print(f"\n✅ FILE EXISTS: {filename}")
        print(f"✅ TOTAL RECORDS: {len(df)}")
        print(f"✅ TOTAL COLUMNS: {len(df.columns)}")
        
        print(f"\n📋 COLUMN VERIFICATION:")
        all_columns_present = True
        for col in required_columns:
            if col in df.columns:
                print(f"  ✅ {col}")
            else:
                print(f"  ❌ {col} - MISSING")
                all_columns_present = False
        
        if all_columns_present:
            print(f"\n✅ ALL REQUIRED COLUMNS PRESENT")
        else:
            print(f"\n❌ SOME REQUIRED COLUMNS MISSING")
        
        # Show data quality stats
        print(f"\n📊 DATA QUALITY STATISTICS:")
        for col in required_columns:
            if col in df.columns:
                non_empty = df[col].notna().sum() if col in df.columns else 0
                filled_percentage = (non_empty / len(df)) * 100 if len(df) > 0 else 0
                print(f"  {col}: {non_empty}/{len(df)} filled ({filled_percentage:.1f}%)")
        
        # Show sample records
        print(f"\n📋 SAMPLE RECORDS (First 3):")
        print("-" * 60)
        for i, row in df.head(3).iterrows():
            print(f"Record {i+1}:")
            print(f"  Title: {row['JobTitle']}")
            print(f"  Location: {row['Location']}")
            print(f"  Experience: {row['ExperienceRequired']}")
            print(f"  Skills: {row['SkillsRequired'][:50]}..." if len(str(row['SkillsRequired'])) > 50 else f"  Skills: {row['SkillsRequired']}")
            print(f"  URL: {row['JobURL'][:50]}..." if len(str(row['JobURL'])) > 50 else f"  URL: {row['JobURL']}")
            print()
        
        # Verify no index column
        if df.index.name is None and not any('Unnamed' in str(col) for col in df.columns):
            print("✅ NO INDEX COLUMN IN EXCEL FILE")
        else:
            print("⚠️  Index column may be present")
        
        print("=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {str(e)}")
        return False

if __name__ == "__main__":
    verify_excel_file("TechCompany_Jobs.xlsx")
