import json
import os
from collections import defaultdict
from SaranaModule.pengekstrak_kata_kunci import DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT # Added import

def load_json_data(file_path):
    """
    Opens and loads JSON data from the file.
    Handles FileNotFoundError and other JSON loading errors gracefully.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: File tidak ditemukan di {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Gagal mendekode JSON dari file {file_path}. Pastikan format JSON valid.")
        return None
    except Exception as e:
        print(f"Error tidak terduga saat memuat file JSON {file_path}: {e}")
        return None

def assign_heuristic_scores(extracted_item, all_known_keywords_config):
    """
    Assigns a heuristic score based on whether a keyword was extracted.
    Inputs:
        extracted_item: A dictionary like {'nama_file': 'doc1.pdf', 'hasil_ekstraksi': {'Keyword1': 123.0, ...}}.
                        Note: 'hasil_ekstraksi' is the key used in the main notebook's output list.
        all_known_keywords_config: List of keyword configuration dicts (like DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT).
    Output: A list of dictionaries, each being {'kata_kunci': str, 'nama_file': str, 'skor_heuristik': float, 'nilai_ekstrak': any}.
    """
    if not isinstance(extracted_item, dict) or 'nama_file' not in extracted_item or 'hasil_ekstraksi' not in extracted_item:
        print(f"Peringatan: Format item ekstraksi tidak valid: {extracted_item}. Melewati.")
        return []

    nama_file = extracted_item['nama_file']
    # hasil_ekstraksi_dokumen refers to the dict like {'Keyword1': 123.0, ...}
    hasil_ekstraksi_dokumen = extracted_item['hasil_ekstraksi'] 
    
    if not isinstance(hasil_ekstraksi_dokumen, dict):
        print(f"Peringatan: 'hasil_ekstraksi' dalam item untuk file {nama_file} bukan dictionary. Melewati.")
        return []

    scored_keywords_list = []

    for keyword_info in all_known_keywords_config:
        kata_dasar = keyword_info['kata_dasar']
        nilai_ekstrak = hasil_ekstraksi_dokumen.get(kata_dasar)

        if nilai_ekstrak is not None:
            skor = 0.75  # Keyword extracted
        else:
            skor = 0.25  # Keyword not extracted
        
        scored_keywords_list.append({
            'kata_kunci': kata_dasar,
            'nama_file': nama_file,
            'skor_heuristik': skor,
            'nilai_ekstrak': nilai_ekstrak 
        })
    return scored_keywords_list

def prepare_roc_data(all_scored_items, ground_truth_dir_path):
    """
    Prepares data for ROC curve generation for global keyword detection.
    Inputs:
        all_scored_items: A flat list from assign_heuristic_scores across all documents.
        ground_truth_dir_path: Path to the ground truth directory.
    Output: A dictionary {'roc_points': list_of_tuples_fpr_tpr, 'auc': float}.
    """
    roc_input_list = []
    all_gt_data = {}

    # Pre-load all ground truth data
    # Get unique filenames from all_scored_items to avoid redundant loading
    unique_files_in_scores = set(item['nama_file'] for item in all_scored_items)

    for nama_file in unique_files_in_scores:
        gt_file_name = os.path.splitext(nama_file)[0] + '.json'
        gt_file_path = os.path.join(ground_truth_dir_path, gt_file_name)
        gt_content = load_json_data(gt_file_path)
        if gt_content and isinstance(gt_content, dict) and "ground_truth_data" in gt_content and \
           isinstance(gt_content["ground_truth_data"], dict):
            all_gt_data[nama_file] = gt_content["ground_truth_data"]
        else:
            print(f"Peringatan: Ground truth untuk file {nama_file} tidak ditemukan atau formatnya salah di {gt_file_path}. Item dari file ini akan dilewati untuk ROC.")

    # Create list of (score, is_positive_in_gt)
    for item in all_scored_items:
        skor = item['skor_heuristik']
        kata_kunci = item['kata_kunci']
        nama_file = item['nama_file']
        
        doc_gt = all_gt_data.get(nama_file)
        if doc_gt is not None: # Only process if GT for this file was successfully loaded
            is_positive_in_gt = kata_kunci in doc_gt # Key existence means it's a positive for detection
            roc_input_list.append((skor, is_positive_in_gt))
        # If doc_gt is None, items for this file are skipped (warning already printed)

    if not roc_input_list:
        print("Peringatan ROC: Tidak ada data input untuk ROC setelah mencocokkan dengan ground truth.")
        return {'roc_points': [(0.0, 0.0), (1.0, 1.0)], 'auc': 0.5, 'info': 'No valid data for ROC'}


    # Sort by score (descending), then by is_positive_in_gt (descending - True before False for tie-breaking)
    # This specific tie-breaking (True before False) helps in correctly forming plateaus if needed,
    # but standard AUC calculation is robust to various tie-breaking at same score.
    roc_input_list.sort(key=lambda x: (x[0], x[1]), reverse=True)

    total_P = sum(1 for _, is_positive in roc_input_list if is_positive)
    total_N = len(roc_input_list) - total_P

    if total_P == 0 or total_N == 0:
        info_auc = f"AUC tidak dapat dihitung secara definitif (total_P={total_P}, total_N={total_N})."
        print(f"Peringatan ROC: {info_auc}")
        # Return a diagonal line and AUC 0.5, or could be 0 or 1 if one class is absent and all predictions are for the other.
        # For simplicity, if one class is absent, the ability to discriminate is minimal.
        return {'roc_points': [(0.0, 0.0), (1.0, 1.0)], 'auc': 0.5, 'info': info_auc}

    roc_points = [(0.0, 0.0)]
    current_tp = 0
    current_fp = 0
    
    # Iterate through sorted list to build ROC points
    # The standard algorithm processes points based on unique threshold values (scores).
    # If multiple items have the same score, they are processed together.
    
    idx = 0
    while idx < len(roc_input_list):
        score_threshold = roc_input_list[idx][0]
        
        # Process all items with this score_threshold
        # For items with this score, count how many are P and how many are N
        # This is slightly different from iterating one by one if scores are not unique.
        # However, iterating one-by-one and adding points when score changes is also common.
        # Let's stick to the common algorithm: iterate, and if score changes, add point.
        # The sorting ensures TPs are generally processed before FPs for the same score if sorted by label too.

        # A simpler way for distinct points:
        # Iterate through each item. If it's positive, TP increases. If negative, FP increases.
        # Add a point (FP/total_N, TP/total_P) after each item or group of items with same score.
        # To handle groups with the same score correctly and avoid jagged lines:
        
        # We add a point *before* processing items at a new, lower score threshold.
        # The first point (0,0) is already added.
        
        # Simplified loop based on common ROC algorithm:
        # Iterate through each prediction. If it's a positive, TP++. Else FP++.
        # This might create more points than strictly necessary if multiple items have same score,
        # but AUC calculation (trapezoidal rule) handles it.
        # A more refined approach groups by score, but this is also valid.
        
        # Let's refine to handle score groups for cleaner ROC points list
        # Add points when the score *changes*.
        
        temp_tp = current_tp
        temp_fp = current_fp

        # Process all items with the current score_threshold
        # This loop finds all items matching current score_threshold
        start_idx = idx
        while idx < len(roc_input_list) and roc_input_list[idx][0] == score_threshold:
            if roc_input_list[idx][1]: # is_positive
                current_tp +=1
            else:
                current_fp +=1
            idx +=1
        
        # Add point *after* processing all items at this threshold
        # unless it's the same as the last point (can happen if only FPs or TPs are added at a threshold)
        new_point = (current_fp / total_N, current_tp / total_P)
        if new_point != roc_points[-1]:
             roc_points.append(new_point)
        
    # Ensure the last point is (1.0, 1.0) if not already
    # This should naturally occur if current_fp == total_N and current_tp == total_P
    if roc_points[-1] != (1.0, 1.0) and abs(roc_points[-1][0] - 1.0) < 1e-9 and abs(roc_points[-1][1] - 1.0) < 1e-9 :
        roc_points[-1] = (1.0,1.0) # Correct floating point inaccuracies
    elif roc_points[-1] != (1.0, 1.0):
        # This might happen if last items were all TP or all FP leading to last point not being exactly (1,1)
        # due to how points are added.
        # Forcibly add (1,1) if the loop finished and current_fp/N and current_tp/P is not (1,1)
        # but should be. This usually means the loop structure for adding points might need one final addition.
        # The current logic should correctly end up at (total_N/total_N, total_P/total_P) = (1,1)
        # Let's ensure it's added if the list doesn't end with it.
         if current_fp == total_N and current_tp == total_P and roc_points[-1] != (1.0,1.0):
            roc_points.append((1.0,1.0))


    # Calculate AUC using the trapezoidal rule
    auc = 0.0
    for i in range(len(roc_points) - 1):
        auc += (roc_points[i+1][0] - roc_points[i][0]) * (roc_points[i+1][1] + roc_points[i][1]) / 2.0
    
    return {'roc_points': roc_points, 'auc': auc}


def compare_results(extracted_data_list, ground_truth_dir_path):
    """
    Compares extracted data with ground truth data to calculate accuracy metrics,
    including Precision, Recall, and F1-score for keyword detection.
    """
    if not extracted_data_list:
        print("Error: Daftar data ekstraksi kosong atau None.")
        return {}

    keyword_detection_counts = defaultdict(int) 
    exact_match_counts = defaultdict(int)      
    sum_absolute_errors = defaultdict(float)
    sum_percentage_errors = defaultdict(float)
    keyword_ground_truth_occurrences = defaultdict(int) 
    keyword_numeric_value_pairs_count = defaultdict(int) 

    keyword_tp = defaultdict(int) 
    keyword_fp = defaultdict(int) 
    keyword_fn = defaultdict(int) 
    
    all_processed_keywords = set() # Keep track of all keywords encountered for comprehensive final reporting

    # Initialize counters for overall aggregate accuracy
    total_ground_truth_keywords = 0
    total_correctly_extracted_with_correct_values = 0

    for item_ekstraksi in extracted_data_list:
        if not isinstance(item_ekstraksi, dict):
            print(f"Peringatan: Melewati item ekstraksi (bukan dictionary): {item_ekstraksi}")
            continue
            
        nama_file = item_ekstraksi.get("nama_file")
        # Key changed from 'kamus_hasil_ekstraksi_file' to 'hasil_ekstraksi' in previous notebook modification
        hasil_ekstraksi_dokumen = item_ekstraksi.get("hasil_ekstraksi") 

        if not nama_file or not isinstance(hasil_ekstraksi_dokumen, dict):
            print(f"Peringatan: Melewati item ekstraksi karena 'nama_file' atau 'hasil_ekstraksi' tidak valid: {nama_file}")
            continue
        
        # Check for error flags from extraction
        is_extraction_error = False
        for error_key in ["error_parsing", "error_runtime_ekstraksi", "error_konfigurasi_global", "error_global_konfigurasi"]:
            if hasil_ekstraksi_dokumen.get(error_key):
                is_extraction_error = True
                break
        if hasil_ekstraksi_dokumen.get("info_parsing") and "kosong" in hasil_ekstraksi_dokumen["info_parsing"]:
            is_extraction_error = True # Treat empty text as a case to skip for detailed eval

        if is_extraction_error:
            print(f"Info: Melewati evaluasi detail untuk file '{nama_file}' karena error/info pada tahap ekstraksi: {hasil_ekstraksi_dokumen}")
            # Still, all its potential keywords (from DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT) could be considered FN if not scored later for ROC
            # However, the current ROC prep logic relies on `assign_heuristic_scores` which uses `hasil_ekstraksi_dokumen`.
            # If `hasil_ekstraksi_dokumen` is an error dict, `assign_heuristic_scores` will give all keywords score 0.25.
            # This is acceptable for now.
            continue


        ground_truth_file_name = os.path.splitext(nama_file)[0] + '.json'
        ground_truth_file_path = os.path.join(ground_truth_dir_path, ground_truth_file_name)
        ground_truth_data_container = load_json_data(ground_truth_file_path)

        current_file_gt_dict = {}
        if ground_truth_data_container and \
           isinstance(ground_truth_data_container, dict) and \
           "ground_truth_data" in ground_truth_data_container and \
           isinstance(ground_truth_data_container["ground_truth_data"], dict):
            current_file_gt_dict = ground_truth_data_container["ground_truth_data"]
        else:
            if ground_truth_data_container is not None: # load_json_data would have printed if None
                 print(f"Peringatan (compare_results): GT untuk file {nama_file} tidak ditemukan/valid di {ground_truth_file_path}. Tidak dapat melakukan perbandingan untuk file ini.")
            # If no GT for this file, we can't calculate TP/FN for its keywords accurately based on this file.
            # FP can still be identified if extracted_keywords are not in an empty current_file_gt_dict.
            # For simplicity in this iteration, if GT for a file is missing, we skip detailed metrics for it.
            # ROC data preparation will also naturally skip it if `all_gt_data` doesn't include this file.
            continue 
        
        # print(f"\nMemproses file untuk evaluasi P/R/F1: {nama_file}")
        
        # Update all_processed_keywords with keys from current GT and extraction
        for k_gt in current_file_gt_dict.keys(): all_processed_keywords.add(k_gt)
        # Add extracted keys that are not errors/info messages
        for k_ex in hasil_ekstraksi_dokumen.keys():
            if not k_ex.startswith("error_") and not k_ex.startswith("info_"):
                 all_processed_keywords.add(k_ex)


        # Iterate through ground truth keys for TP and FN for *this file*
        for kata_kunci_gt, nilai_gt in current_file_gt_dict.items():
            total_ground_truth_keywords += 1 # Increment for each GT keyword
            keyword_ground_truth_occurrences[kata_kunci_gt] += 1 
            nilai_ekstrak = hasil_ekstraksi_dokumen.get(kata_kunci_gt)
            
            # For P/R/F1 of keyword *detection*:
            # A keyword is considered "detected" if it's a key in hasil_ekstraksi_dokumen
            # and its value is not None (meaning it was actively extracted, not just absent).
            if nilai_ekstrak is not None:
                keyword_tp[kata_kunci_gt] += 1
                keyword_detection_counts[kata_kunci_gt] += 1 # For original detection rate metric
                
                if nilai_gt is not None and nilai_ekstrak == nilai_gt: # Exact value match
                    exact_match_counts[kata_kunci_gt] += 1
                    total_correctly_extracted_with_correct_values += 1 # Increment for correct value match
                
                is_nilai_gt_numeric = isinstance(nilai_gt, (int, float))
                is_nilai_ekstrak_numeric = isinstance(nilai_ekstrak, (int, float))

                if is_nilai_gt_numeric and is_nilai_ekstrak_numeric:
                    keyword_numeric_value_pairs_count[kata_kunci_gt] += 1
                    sum_absolute_errors[kata_kunci_gt] += abs(float(nilai_ekstrak) - float(nilai_gt))
                    if float(nilai_gt) != 0:
                        sum_percentage_errors[kata_kunci_gt] += abs((float(nilai_ekstrak) - float(nilai_gt)) / float(nilai_gt)) * 100
                    elif float(nilai_ekstrak) != 0: # GT is 0, extracted is not 0
                        sum_percentage_errors[kata_kunci_gt] += 100.0 
            else: # Not extracted, or extracted as None
                keyword_fn[kata_kunci_gt] += 1

        # Iterate through extracted keys for FP for *this file*
        for kata_kunci_ekstrak, nilai_ekstrak_val in hasil_ekstraksi_dokumen.items():
            # Ensure it's a real keyword, not an error/info message from extraction
            if kata_kunci_ekstrak.startswith("error_") or kata_kunci_ekstrak.startswith("info_"):
                continue
            if nilai_ekstrak_val is not None: # Must have a non-None value to be considered "extracted"
                if kata_kunci_ekstrak not in current_file_gt_dict:
                    keyword_fp[kata_kunci_ekstrak] += 1

    final_metrics = {}
    all_unique_keywords_overall = set(DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT_FLAT) | \
                                  all_processed_keywords | \
                                  set(keyword_tp.keys()) | \
                                  set(keyword_fp.keys()) | \
                                  set(keyword_fn.keys())


    for k in all_unique_keywords_overall:
        final_metrics[k] = {}
        
        tp = keyword_tp[k]
        fp = keyword_fp[k]
        fn = keyword_fn[k]

        if (tp + fp) == 0: precision = 0.0
        else: precision = tp / (tp + fp)
        
        if (tp + fn) == 0: recall = 0.0
        else: recall = tp / (tp + fn)
            
        if (precision + recall) == 0: f1_score = 0.0
        else: f1_score = 2 * (precision * recall) / (precision + recall)
            
        final_metrics[k]['precision'] = precision * 100
        final_metrics[k]['recall'] = recall * 100
        final_metrics[k]['f1_score'] = f1_score * 100

        if keyword_ground_truth_occurrences[k] > 0:
            final_metrics[k]['detection_rate'] = (keyword_detection_counts[k] / keyword_ground_truth_occurrences[k]) * 100
            final_metrics[k]['exact_value_match_accuracy'] = (exact_match_counts[k] / keyword_ground_truth_occurrences[k]) * 100
        else: 
            final_metrics[k]['detection_rate'] = 'N/A (GT Occurrences=0)'
            final_metrics[k]['exact_value_match_accuracy'] = 'N/A (GT Occurrences=0)'
        
        if keyword_numeric_value_pairs_count[k] > 0:
            final_metrics[k]['mean_absolute_error'] = sum_absolute_errors[k] / keyword_numeric_value_pairs_count[k]
            final_metrics[k]['mean_percentage_error'] = sum_percentage_errors[k] / keyword_numeric_value_pairs_count[k]
        else:
            final_metrics[k]['mean_absolute_error'] = 'N/A (No Numeric Pairs)'
            final_metrics[k]['mean_percentage_error'] = 'N/A (No Numeric Pairs)'
            
        final_metrics[k]['gt_occurrences'] = keyword_ground_truth_occurrences[k]
        # detected_occurrences_in_gt_context changed to keyword_detection_counts to reflect its original meaning
        final_metrics[k]['detected_in_gt_context_count'] = keyword_detection_counts[k] 
        final_metrics[k]['numeric_pairs_found'] = keyword_numeric_value_pairs_count[k]
        final_metrics[k]['exact_value_matches'] = exact_match_counts[k]
        final_metrics[k]['tp'] = tp
        final_metrics[k]['fp'] = fp
        final_metrics[k]['fn'] = fn
    
    # Calculate and store overall aggregate accuracy
    if total_ground_truth_keywords == 0:
        aggregate_accuracy_percentage = 0.0 # Or 'N/A' if preferred, but float is better for consistency
    else:
        aggregate_accuracy_percentage = (total_correctly_extracted_with_correct_values / total_ground_truth_keywords) * 100
    
    final_metrics['overall_aggregate_accuracy'] = {
        'accuracy_percentage': aggregate_accuracy_percentage,
        'total_ground_truth_keywords': total_ground_truth_keywords,
        'total_correctly_extracted_with_correct_values': total_correctly_extracted_with_correct_values
    }
        
    return final_metrics

# Helper to get a flat list of all default keyword strings
DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT_FLAT = [item['kata_dasar'] for item in DAFTAR_KATA_KUNCI_KEUANGAN_DEFAULT]
