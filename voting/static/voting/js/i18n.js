/**
 * ChainVote Centralized Internationalization Engine (i18n.js)
 * Supports full bilingual localization between English and Hindi (हिन्दी)
 * across voter-facing and administrative interfaces.
 */

(function () {
    'use strict';

    // ── 1. STATIC UI DICTIONARY ──────────────────────────────────────────
    const translations = {
        en: {
            // Navigation & Brand
            brand_name: 'ChainVote',
            nav_manage: 'Manage',
            nav_ledger: 'Ledger',
            nav_login: 'Log In',
            nav_signout: 'Sign Out',
            nav_soc: 'SOC Dashboard',
            nav_results: 'Results',
            lang_btn: 'हिंदी',
            link_abort: 'Abort & Return',
            link_back_home: 'Back to Home',
            link_back_network: 'Back to Network',
            link_exit_results: 'Exit to Results',

            // Footer
            footer_text: 'Secure & Decentralized Voting Protocol',
            footer_tagline: 'Built for the Hackathon • Secure & Decentralized Voting Protocol',
            footer_soc: 'SOC Dashboard',

            // Homepage Hero
            hero_title: 'Decentralized.<br>Anonymous.',
            hero_subtitle: 'The next generation of digital democracy. Cast your zero-knowledge vote securely on the immutable ledger.',

            // Security Threat Warning (Homepage)
            sec_alert_title: 'Security Notice',
            sec_alert_desc: 'A security threat event was detected and mitigated by the protocol. Blockchain ledger integrity remains secure.',
            lbl_logged: 'Logged:',

            // 4-Step Instructions (Homepage)
            steps_heading: 'How to Cast Your Vote',
            steps_subheading: 'Follow these 4 simple steps to participate in any election',
            steps_badge: 'Simple & Secure',
            step1_title: '1. Choose Election',
            step1_desc: 'Select an available active election below and enter the voting booth.',
            step2_title: '2. Verify Voter ID',
            step2_desc: 'Enter your valid 10-character Voter ID to verify voter eligibility.',
            step3_title: '3. Select Candidate',
            step3_desc: 'Review the candidate roster and select your preferred candidate.',
            step4_title: '4. Review & Confirm',
            step4_desc: 'Review your ballot selection and submit your encrypted vote.',

            // Election Sections (Homepage)
            active_elections_title: 'Active Elections',
            active_elections_sub: 'Currently open for voting',
            badge_live: 'Live Now',
            status_active: 'Active',
            closes_in: 'Closes in',
            candidates_label: 'Candidates:',
            btn_enter_booth: 'Enter Booth →',
            no_active_elections: 'No active elections at this time.',

            archived_title: 'Past Elections',
            status_completed: 'Completed',
            total_votes_label: 'total votes recorded',
            btn_results: 'Results',
            btn_audit: 'Audit Chain',
            audit_restricted_title: 'Ledger auditing is restricted to administrative oversight',
            no_archived: 'No archived data.',

            scheduled_title: 'Upcoming Elections',
            status_upcoming: 'Upcoming',
            starts_on: 'Starts',
            no_upcoming: 'No upcoming events.',

            // Security Trust Section (Homepage)
            security_heading: 'Engineered for absolute trust.',
            security_subheading: 'ChainVote uses decentralized cryptography to guarantee mathematical integrity without compromising voter privacy.',
            sec1_title: 'Zero-Knowledge Privacy',
            sec1_desc: 'Your identity is securely hashed client-side. We verify eligibility without ever knowing or saving who you actually voted for.',
            sec2_title: 'Tamper-Proof Ledger',
            sec2_desc: 'Every vote forms a mathematically linked block in the ledger chain. Once confirmed, results cannot be altered or deleted.',
            sec3_title: 'Active Threat SOC',
            sec3_desc: 'A live Security Operations Center monitors and blocks duplicate voting attempts and anomalies in real-time.',

            // Voting Booth (election_detail.html)
            badge_active_booth: 'Active Voting Booth',
            step1_heading: 'Verify Your Identity',
            label_voter_id: 'Unique Voter ID (Aadhaar / Roll No.)',
            ph_voter_id: 'Enter 10-character ID...',
            zkp_explanation: 'Privacy Protected: Your ID is converted into a secure one-way hash. Your raw ID is never stored.',
            step2_heading: 'Select Candidate',
            select_candidate_hint: 'Choose one candidate from the options below:',
            btn_review: 'Review Your Vote →',

            // Review Modal (election_detail.html)
            modal_review_title: 'Review Your Ballot',
            modal_review_subtitle: 'Confirm your choice before it is committed to the blockchain',
            review_election_lbl: 'Election',
            review_selected_candidate_lbl: 'Selected Candidate',
            review_voter_id_lbl: 'Voter Identifier',
            badge_masked: 'Masked',
            badge_encrypted: 'Masked',
            review_notice: 'Note: Once confirmed, your vote is permanently recorded and cannot be altered or re-cast.',
            btn_change_selection: '← Change Selection',
            btn_confirm_submit: 'Confirm & Submit Vote',
            recording_vote: 'Encrypting & Recording Vote...',

            // Client-side Validation Messages
            field_voter_id_required: 'Voter ID is required.',
            alert_enter_id: 'Please enter your Unique Voter ID before proceeding.',
            alert_invalid_id: 'Voter ID must contain both letters and numbers (alphanumeric only).',
            alert_select_candidate: 'Please select a candidate before proceeding.',
            validation_alert_incomplete: 'Please complete all fields before reviewing your vote.',

            // Receipt Modal (election_detail.html & receipt.html)
            receipt_heading: 'Vote Successfully Cast!',
            receipt_title_official: 'Official Voting Receipt',
            receipt_status_lbl: 'Network Status',
            receipt_mined_msg: 'Block Mined Successfully',
            receipt_election_lbl: 'Election Title',
            receipt_time_lbl: 'Timestamp (Local)',
            receipt_note: 'Please save or print this official confirmation. Your voter identity is protected by zero-knowledge hashing.',
            receipt_save_note: '* Please save this receipt. You can use your Block Hash to verify your vote was permanently recorded on the blockchain without revealing your identity.',
            btn_print_receipt: 'Print Receipt',
            btn_return_network: 'Return to Network',
            btn_return_home: 'Return to Home →',
            lbl_time_cast: 'Time Cast',
            lbl_anon_voter_hash: 'Your Anonymous Voter Hash',
            lbl_block_hash_receipt: 'Your Block Hash (Ledger ID)',
            btn_print_pdf: 'Print / Save PDF',

            // Results Page (results.html)
            results_page_title: 'Election Results',
            status_concluded: 'Election Concluded',
            status_active_results: 'Election Active',
            lbl_total_votes: 'Total Votes Cast',
            lbl_end_time_utc: 'End Time (UTC)',
            sealed_title: 'Cryptographic Lock Active',
            sealed_desc: 'To guarantee absolute integrity, results are encrypted on the blockchain and cannot be decrypted or tallied until the election officially concludes.',
            sealed_badge: 'Immutable Ledger Sealed',
            tally_title: 'Final Ledger Tally',
            badge_winner: 'Winner',
            lbl_votes: 'Votes',
            btn_audit_ledger: 'Audit Blockchain Ledger',

            // Explorer Page (explorer.html)
            explorer_title: 'Ledger Explorer',
            ph_hash_search: 'Paste Voter Hash or Block Hash to audit...',
            btn_verify_integrity: 'Verify Integrity',
            msg_block_found: '✓ Cryptographic block found on the public ledger.',
            lbl_block_num: 'Block #',
            lbl_sha_link: 'SHA-256 Link',
            lbl_prev_hash: 'Linked Previous Hash',
            lbl_encrypted_payload: 'Encrypted Payload (AES-256)',
            lbl_generated_block_hash: 'Generated Block Hash',
            btn_copy: 'Copy',
            lbl_copied: 'Copied!',
            empty_ledger_title: 'Ledger is Empty',
            empty_ledger_desc: 'Waiting for the Genesis Block to be mined...',

            // Threat Operations / SOC Dashboard (threat_dashboard.html)
            badge_soc_active: 'SOC Active',
            soc_title: 'Threat Operations',
            soc_subtitle: 'Real-time monitoring of network anomalies, duplicate vote attempts, and unauthorized blockchain access.',
            lbl_prevented_attacks: 'Total Prevented Attacks',
            soc_table_heading: 'Live Security Event Log',
            th_timestamp_local: 'Timestamp (Local)',
            th_severity: 'Severity',
            th_origin_ip: 'Origin IP',
            th_action_triggered: 'Action Triggered',
            th_trace_details: 'Trace Details',
            severity_critical: 'CRITICAL',
            severity_warning: 'WARNING',
            no_security_events: 'No security incidents logged.',

            // Authentication (login.html & register.html)
            login_title: 'Welcome Back',
            login_subtitle: 'Sign in to access the Election Management Portal',
            label_username: 'Username',
            ph_username: 'Enter your username',
            label_password: 'Password',
            ph_password: 'Enter your password',
            btn_signin: 'Sign In →',
            register_title: 'Register New Account',
            register_subtitle: 'Create administrative credentials for election management',
            hint_username: 'Letters and numbers only, no spaces',
            label_email: 'Email Address',
            ph_email: 'Enter your email',
            label_confirm_password: 'Confirm Password',
            ph_confirm_password: 'Confirm your password',
            hint_password: 'Minimum 8 characters recommended',
            label_password2: 'Confirm Password',
            ph_password2: 'Repeat your password',
            btn_register: 'Register →',
            already_account_text: 'Already have an account?',
            link_signin: 'Sign in here',

            // Admin Manage Dashboard (manage/dashboard.html)
            admin_badge: 'Administrative Management',
            admin_dashboard_title: 'Election Management Portal',
            admin_dashboard_sub: 'Configure elections, review schedules, and manage candidate rosters.',
            btn_jump_ledger: 'Blockchain Ledger',
            btn_jump_soc: 'SOC Operations',
            btn_create_election: 'Create New Election',
            metric_total_elections: 'Total Elections',
            metric_active_now: 'Active Now',
            metric_completed: 'Completed',
            metric_total_candidates: 'Total Candidates',
            roster_heading: 'Elections Roster',
            roster_subheading: 'Protected against deletion to preserve cryptographic ledger integrity',
            th_election: 'Election',
            th_status: 'Status',
            th_schedule: 'Schedule',
            th_candidates: 'Candidates',
            th_votes_recorded: 'Votes Recorded',
            th_actions: 'Actions',
            lbl_start: 'Start:',
            lbl_end: 'End:',
            btn_manage_candidates: 'Candidates',
            btn_edit: 'Edit',
            btn_delete: 'Delete',
            btn_delete_locked: 'Delete Locked',
            lbl_candidates_unit: 'candidates',
            lbl_no_description: 'No description provided',
            soc_section_title: 'Security Operations Center (SOC)',
            soc_section_sub: 'Active telemetry monitoring voting patterns, replay attempts, and cryptographic integrity',
            lbl_threats_blocked: 'Threats Blocked',
            lbl_active_sensors: 'Active Sensors',
            lbl_system_status: 'System Status',
            lbl_operational: 'OPERATIONAL',

            // Dedicated Blockchain Ledger (manage/ledger.html)
            ledger_badge: 'Cryptographic Audit',
            ledger_title: 'Visual Blockchain Ledger',
            ledger_sub: 'Immutable cryptographic block sequence verifying end-to-end voting integrity',
            btn_back_dashboard: 'Back to Dashboard',
            lbl_total_blocks_mined: 'Total Blocks Mined',
            lbl_verified_chains: 'Verified Chains',
            lbl_tamper_events: 'Tamper Events',
            lbl_ledger_status: 'Ledger Status',
            ph_search_ledger: 'Search by block hash, voter hash, or ID...',
            filter_all_chains: 'All Chains',
            lbl_genesis_block: 'Genesis Block',
            lbl_timestamp_utc: 'Timestamp (UTC)',
            lbl_election_label: 'Election',
            lbl_voter_identity_hash: 'Voter Identity Hash',
            lbl_encrypted_vote_payload: 'Encrypted Vote Payload',
            lbl_previous_block_hash: 'Previous Block Hash',
            lbl_block_hash_sha256: 'Block Hash (SHA-256)',
            lbl_chain_verified: 'Chain Integrity Verified',

            // Candidate Management (manage/candidates.html & forms)
            manage_candidates_title: 'Manage Candidates',
            manage_candidates_sub: 'Configure official candidate roster for this election',
            btn_add_candidate: 'Add Candidate',
            th_candidate_name: 'Candidate Name',
            th_party_description: 'Party / Description',
            no_candidates_yet: 'No candidates added yet.',
            candidate_form_title_add: 'Add Candidate',
            candidate_form_title_edit: 'Edit Candidate',
            label_candidate_name: 'Candidate Name',
            ph_candidate_name: 'e.g. Aarav Sharma',
            label_candidate_desc: 'Party / Description',
            ph_candidate_desc: 'e.g. Digital India Party',
            btn_save_candidate: 'Save Candidate',
            btn_cancel: 'Cancel',

            // Election Form (manage/election_form.html)
            election_form_title_create: 'Create New Election',
            election_form_title_edit: 'Edit Election',
            label_election_title: 'Election Title',
            ph_election_title: 'e.g. 2026 National Election',
            label_election_desc: 'Description',
            ph_election_desc: 'Provide details about this election...',
            label_start_time: 'Start Time (UTC)',
            label_end_time: 'End Time (UTC)',
            btn_save_election: 'Save Election',

            // Delete Confirmations (manage/confirm_delete)
            delete_election_title: 'Confirm Election Deletion',
            delete_election_warning: 'Are you sure you want to delete election:',
            delete_candidate_title: 'Confirm Candidate Deletion',
            delete_candidate_warning: 'Are you sure you want to delete candidate:',
            btn_confirm_delete_election: 'Delete Election',
            btn_confirm_delete_candidate: 'Delete Candidate',
            btn_cancel_return: 'Cancel & Return'
        },

        hi: {
            // Navigation & Brand
            brand_name: 'चेनवोट',
            nav_manage: 'प्रबंधन',
            nav_ledger: 'लेज़र',
            nav_login: 'लॉग इन',
            nav_signout: 'लॉग आउट',
            nav_soc: 'SOC डैशबोर्ड',
            nav_results: 'परिणाम',
            lang_btn: 'English',
            link_abort: 'वापस जाएं (रद्द करें)',
            link_back_home: 'होमपेज पर लौटें',
            link_back_network: 'नेटवर्क पर वापस जाएं',
            link_exit_results: 'परिणाम पर जाएं',

            // Footer
            footer_text: 'सुरक्षित एवं विकेंद्रीकृत मतदान प्रणाली',
            footer_tagline: 'हैकथॉन के लिए निर्मित • सुरक्षित एवं विकेंद्रीकृत मतदान प्रणाली',
            footer_soc: 'SOC सुरक्षा डैशबोर्ड',

            // Homepage Hero
            hero_title: 'विकेंद्रीकृत।<br>पूर्णतः गोपनीय।',
            hero_subtitle: 'डिजिटल लोकतंत्र की नई पीढ़ी। अपरिवर्तनीय डिजिटल बहीखाते (लेजर) पर अपना गोपनीय एवं सुरक्षित मत दर्ज करें।',

            // Security Threat Warning (Homepage)
            sec_alert_title: 'सुरक्षा सूचना',
            sec_alert_desc: 'एक सुरक्षा खतरे का पता चला और उसे प्रोटोकॉल द्वारा निष्प्रभावी कर दिया गया। ब्लॉकचेन लेज़र सुरक्षित है।',
            lbl_logged: 'दर्ज:',

            // 4-Step Instructions (Homepage)
            steps_heading: 'वोट कैसे डालें?',
            steps_subheading: 'किसी भी चुनाव में भाग लेने के लिए इन 4 सरल चरणों का पालन करें',
            steps_badge: 'सरल एवं सुरक्षित',
            step1_title: '1. चुनाव चुनें',
            step1_desc: 'नीचे उपलब्ध चालू चुनाव का चयन करें और मतदान कक्ष में प्रवेश करें।',
            step2_title: '2. वोटर आईडी सत्यापित करें',
            step2_desc: 'मतदान पात्रता सत्यापित करने के लिए अपनी मान्य 10-अंकीय वोटर आईडी दर्ज करें।',
            step3_title: '3. उम्मीदवार चुनें',
            step3_desc: 'उम्मीदवारों की सूची की समीक्षा करें और अपने पसंदीदा उम्मीदवार का चयन करें।',
            step4_title: '4. समीक्षा व पुष्टि करें',
            step4_desc: 'अपने मतपत्र की समीक्षा करें और अपना एन्क्रिप्टेड वोट सुरक्षित रूप से दर्ज करें।',

            // Election Sections (Homepage)
            active_elections_title: 'चालू चुनाव',
            active_elections_sub: 'मतदान के लिए अभी खुले हैं',
            badge_live: 'लाइव',
            status_active: 'चालू',
            closes_in: 'समाप्त होने में:',
            candidates_label: 'उम्मीदवार:',
            btn_enter_booth: 'वोट डालें →',
            no_active_elections: 'वर्तमान में कोई चालू चुनाव नहीं है।',

            archived_title: 'समाप्त चुनाव',
            status_completed: 'समाप्त',
            total_votes_label: 'कुल वोट दर्ज',
            btn_results: 'परिणाम देखें',
            btn_audit: 'लेजर ऑडिट',
            audit_restricted_title: 'लेज़र ऑडिट प्रशासनिक निगरानी के लिए प्रतिबंधित है',
            no_archived: 'कोई पुराना डेटा नहीं है।',

            scheduled_title: 'आगामी चुनाव',
            status_upcoming: 'आगामी',
            starts_on: 'प्रारंभ तिथि:',
            no_upcoming: 'कोई आगामी चुनाव नहीं है।',

            // Security Trust Section (Homepage)
            security_heading: 'पूर्ण विश्वास के लिए डिज़ाइन किया गया।',
            security_subheading: 'चेनवोट मतदाता की गोपनीयता से समझौता किए बिना गणितीय निष्पक्षता सुनिश्चित करने के लिए क्रिप्टोग्राफी का उपयोग करता है।',
            sec1_title: 'शून्य-ज्ञान गोपनीयता (ZKP)',
            sec1_desc: 'आपकी पहचान तुरंत कोडित (हैश) हो जाती है। आपकी व्यक्तिगत पसंद कभी भी उजागर नहीं की जाती।',
            sec2_title: 'छेड़छाड़-मुक्त लेजर',
            sec2_desc: 'प्रत्येक वोट ब्लॉकचेन श्रृंखला में एक सुरक्षित ब्लॉक बनाता है। पुष्टि के बाद इसे बदला या मिटाया नहीं जा सकता।',
            sec3_title: 'सक्रिय सुरक्षा निगरानी (SOC)',
            sec3_desc: 'एक लाइव सुरक्षा संचालन केंद्र वास्तविक समय में दोहरे मतदान के प्रयासों और विसंगतियों को रोकता है।',

            // Voting Booth (election_detail.html)
            badge_active_booth: 'सक्रिय मतदान कक्ष',
            step1_heading: 'अपनी पहचान सत्यापित करें',
            label_voter_id: 'विशिष्ट वोटर पहचान (आधार / रोल नंबर)',
            ph_voter_id: '10-अंकीय पहचान दर्ज करें...',
            zkp_explanation: 'गोपनीयता सुरक्षित: आपकी पहचान सुरक्षित कोड में बदली जाती है। आपका मूल नंबर कभी सुरक्षित नहीं किया जाता।',
            step2_heading: 'उम्मीदवार का चयन करें',
            select_candidate_hint: 'नीचे दिए गए विकल्पों में से किसी एक उम्मीदवार को चुनें:',
            btn_review: 'अपने वोट की समीक्षा करें →',

            // Review Modal (election_detail.html)
            modal_review_title: 'अपने मत की समीक्षा करें',
            modal_review_subtitle: 'ब्लॉकचेन पर दर्ज करने से पहले अपनी पसंद की पुष्टि करें',
            review_election_lbl: 'चुनाव',
            review_selected_candidate_lbl: 'चयनित उम्मीदवार',
            review_voter_id_lbl: 'वोटर पहचान',
            badge_masked: 'मास्क किया गया',
            badge_encrypted: 'मास्क किया गया',
            review_notice: 'सूचना: पुष्टि होने के बाद, आपका वोट स्थायी रूप से दर्ज हो जाएगा और इसे बदला नहीं जा सकेगा।',
            btn_change_selection: '← पसंद बदलें',
            btn_confirm_submit: 'पुष्टि करें और वोट दर्ज करें',
            recording_vote: 'वोट सुरक्षित रूप से दर्ज हो रहा है...',

            // Client-side Validation Messages
            field_voter_id_required: 'वोटर आईडी आवश्यक है।',
            alert_enter_id: 'आगे बढ़ने से पहले कृपया अपनी वोटर आईडी दर्ज करें।',
            alert_invalid_id: 'मतदाता आईडी में अक्षर और संख्या दोनों होने चाहिए (केवल अल्फ़ान्यूमेरिक)।',
            alert_select_candidate: 'आगे बढ़ने से पहले कृपया किसी एक उम्मीदवार का चयन करें।',
            validation_alert_incomplete: 'कृपया अपने वोट की समीक्षा करने से पहले सभी फ़ील्ड पूरे करें।',

            // Receipt Modal (election_detail.html & receipt.html)
            receipt_heading: 'मत सफलतापूर्वक दर्ज हुआ!',
            receipt_title_official: 'आधिकारिक मतदान रसीद',
            receipt_status_lbl: 'नेटवर्क स्थिति',
            receipt_mined_msg: 'ब्लॉक सफलतापूर्वक माइन हुआ (Block Mined Successfully)',
            receipt_election_lbl: 'चुनाव का नाम',
            receipt_time_lbl: 'समय (स्थानीय)',
            receipt_note: 'कृपया इस आधिकारिक रसीद को सुरक्षित रखें या प्रिंट करें। शून्य-ज्ञान तकनीक द्वारा आपकी पहचान सुरक्षित है।',
            receipt_save_note: '* कृपया इस रसीद को सहेजें। आप अपनी पहचान उजागर किए बिना ब्लॉकचेन पर अपने वोट की पुष्टि करने के लिए ब्लॉक हैश का उपयोग कर सकते हैं।',
            btn_print_receipt: 'रसीद प्रिंट करें',
            btn_return_network: 'होमपेज पर लौटें',
            btn_return_home: 'होमपेज पर लौटें →',
            lbl_time_cast: 'दर्ज करने का समय',
            lbl_anon_voter_hash: 'आपका गोपनीय वोटर हैश',
            lbl_block_hash_receipt: 'आपका ब्लॉक हैश (लेज़र आईडी)',
            btn_print_pdf: 'प्रिंट / पीडीएफ सहेजें',

            // Results Page (results.html)
            results_page_title: 'चुनाव परिणाम',
            status_concluded: 'चुनाव समाप्त',
            status_active_results: 'चुनाव चालू',
            lbl_total_votes: 'कुल दर्ज वोट',
            lbl_end_time_utc: 'समाप्ति समय (UTC)',
            sealed_title: 'क्रिप्टोग्राफिक लॉक सक्रिय',
            sealed_desc: 'पूर्ण निष्पक्षता सुनिश्चित करने के लिए, परिणाम ब्लॉकचेन पर एन्क्रिप्टेड हैं और चुनाव आधिकारिक रूप से समाप्त होने तक डिक्रिप्ट या गिने नहीं जा सकते।',
            sealed_badge: 'अपरिवर्तनीय लेज़र सीलबंद',
            tally_title: 'अंतिम लेज़र गणना',
            badge_winner: 'विजेता',
            lbl_votes: 'वोट',
            btn_audit_ledger: 'ब्लॉकचेन लेज़र ऑडिट करें',

            // Explorer Page (explorer.html)
            explorer_title: 'लेज़र एक्सप्लोरर',
            ph_hash_search: 'ऑडिट के लिए वोटर हैश या ब्लॉक हैश पेस्ट करें...',
            btn_verify_integrity: 'सत्यता की पुष्टि करें',
            msg_block_found: '✓ सार्वजनिक लेज़र पर ब्लॉक मिल गया।',
            lbl_block_num: 'ब्लॉक #',
            lbl_sha_link: 'SHA-256 लिंक',
            lbl_prev_hash: 'लिंक्ड पिछला हैश',
            lbl_encrypted_payload: 'एन्क्रिप्टेड पेलोड (AES-256)',
            lbl_generated_block_hash: 'जनरेट किया गया ब्लॉक हैश',
            btn_copy: 'कॉपी',
            lbl_copied: 'कॉपी हो गया!',
            empty_ledger_title: 'लेज़र खाली है',
            empty_ledger_desc: 'जेनेसिस ब्लॉक के माइन होने की प्रतीक्षा की जा रही है...',

            // Threat Operations / SOC Dashboard (threat_dashboard.html)
            badge_soc_active: 'SOC सक्रिय',
            soc_title: 'सुरक्षा संचालन (SOC)',
            soc_subtitle: 'नेटवर्क विसंगतियों, दोहरे मतदान के प्रयासों और अनधिकृत पहुंच की वास्तविक समय निगरानी।',
            lbl_prevented_attacks: 'रोके गए कुल हमले',
            soc_table_heading: 'लाइव सुरक्षा इवेंट लॉग',
            th_timestamp_local: 'समय मुहर (स्थानीय)',
            th_severity: 'गंभीरता',
            th_origin_ip: 'उत्पत्ति आईपी',
            th_action_triggered: 'ट्रिगर की गई कार्रवाई',
            th_trace_details: 'ट्रेस विवरण',
            severity_critical: 'गंभीर',
            severity_warning: 'चेतावनी',
            no_security_events: 'कोई सुरक्षा घटना दर्ज नहीं की गई।',

            // Authentication (login.html & register.html)
            login_title: 'वापसी पर स्वागत है',
            login_subtitle: 'चुनाव प्रबंधन पोर्टल तक पहुंचने के लिए साइन इन करें',
            label_username: 'उपयोगकर्ता नाम',
            ph_username: 'अपना उपयोगकर्ता नाम दर्ज करें',
            label_password: 'पासवर्ड',
            ph_password: 'अपना पासवर्ड दर्ज करें',
            btn_signin: 'साइन इन करें →',
            register_title: 'नया खाता पंजीकृत करें',
            register_subtitle: 'चुनाव प्रबंधन के लिए प्रशासनिक साख बनाएं',
            label_email: 'ईमेल पता',
            ph_email: 'अपना ईमेल दर्ज करें',
            label_confirm_password: 'पासवर्ड की पुष्टि करें',
            ph_confirm_password: 'अपने पासवर्ड की पुष्टि करें',
            btn_register: 'पंजीकरण करें →',
            hint_username: 'केवल अक्षर और संख्याएं, रिक्त स्थान नहीं',
            hint_password: 'कम से कम 8 अक्षर अनुशंसित हैं',
            label_password2: 'पासवर्ड की पुष्टि करें',
            ph_password2: 'अपना पासवर्ड दोबारा दर्ज करें',
            already_account_text: 'क्या आपका पहले से खाता है?',
            link_signin: 'यहाँ साइन इन करें',

            // Admin Manage Dashboard (manage/dashboard.html)
            admin_badge: 'प्रशासनिक प्रबंधन',
            admin_dashboard_title: 'चुनाव प्रबंधन पोर्टल',
            admin_dashboard_sub: 'चुनाव कॉन्फ़िगर करें, शेड्यूल की समीक्षा करें और उम्मीदवारों की सूची प्रबंधित करें।',
            btn_jump_ledger: 'ब्लॉकचेन लेज़र',
            btn_jump_soc: 'SOC संचालन',
            btn_create_election: 'नया चुनाव बनाएं',
            metric_total_elections: 'कुल चुनाव',
            metric_active_now: 'अभी चालू',
            metric_completed: 'समाप्त',
            metric_total_candidates: 'कुल उम्मीदवार',
            roster_heading: 'चुनाव सूची',
            roster_subheading: 'क्रिप्टोग्राफिक लेज़र अखंडता बनाए रखने के लिए विलोपन से सुरक्षित',
            th_election: 'चुनाव',
            th_status: 'स्थिति',
            th_schedule: 'शेड्यूल',
            th_candidates: 'उम्मीदवार',
            th_votes_recorded: 'दर्ज वोट',
            th_actions: 'कार्रवाई',
            lbl_start: 'प्रारंभ:',
            lbl_end: 'समाप्ति:',
            btn_manage_candidates: 'उम्मीदवार',
            btn_edit: 'संपादित करें',
            btn_delete: 'हटाएं',
            btn_delete_locked: 'विलोपन लॉक',
            lbl_candidates_unit: 'उम्मीदवार',
            lbl_no_description: 'कोई विवरण उपलब्ध नहीं है',
            soc_section_title: 'सुरक्षा संचालन केंद्र (SOC)',
            soc_section_sub: 'सक्रिय टेलीमेट्री जो मतदान पैटर्न, रीप्ले प्रयासों और क्रिप्टोग्राफिक अखंडता की निगरानी करती है',
            lbl_threats_blocked: 'रोके गए खतरे',
            lbl_active_sensors: 'सक्रिय सेंसर',
            lbl_system_status: 'सिस्टम स्थिति',
            lbl_operational: 'सक्रिय / सुरक्षित',

            // Dedicated Blockchain Ledger (manage/ledger.html)
            ledger_badge: 'क्रिप्टोग्राफिक ऑडिट',
            ledger_title: 'विज़ुअल ब्लॉकचेन लेज़र',
            ledger_sub: 'अपरिवर्तनीय क्रिप्टोग्राफिक ब्लॉक अनुक्रम जो संपूर्ण मतदान अखंडता की पुष्टि करता है',
            btn_back_dashboard: 'डैशबोर्ड पर वापस जाएं',
            lbl_total_blocks_mined: 'कुल माइन किए गए ब्लॉक',
            lbl_verified_chains: 'सत्यापित श्रृंखलाएं',
            lbl_tamper_events: 'छेड़छाड़ की घटनाएं',
            lbl_ledger_status: 'लेज़र स्थिति',
            ph_search_ledger: 'ब्लॉक हैश, वोटर हैश या आईडी द्वारा खोजें...',
            filter_all_chains: 'सभी श्रृंखलाएं',
            lbl_genesis_block: 'जेनेसिस ब्लॉक',
            lbl_timestamp_utc: 'समय मुहर (UTC)',
            lbl_election_label: 'चुनाव',
            lbl_voter_identity_hash: 'वोटर पहचान हैश',
            lbl_encrypted_vote_payload: 'एन्क्रिप्टेड वोट पेलोड',
            lbl_previous_block_hash: 'पिछला ब्लॉक हैश',
            lbl_block_hash_sha256: 'ब्लॉक हैश (SHA-256)',
            lbl_chain_verified: 'श्रृंखला अखंडता सत्यापित',

            // Candidate Management (manage/candidates.html & forms)
            manage_candidates_title: 'उम्मीदवार प्रबंधित करें',
            manage_candidates_sub: 'इस चुनाव के लिए आधिकारिक उम्मीदवारों की सूची कॉन्फ़िगर करें',
            btn_add_candidate: 'नया उम्मीदवार जोड़ें',
            th_candidate_name: 'उम्मीदवार का नाम',
            th_party_description: 'पार्टी / विवरण',
            no_candidates_yet: 'अभी तक कोई उम्मीदवार नहीं जोड़ा गया है।',
            candidate_form_title_add: 'उम्मीदवार जोड़ें',
            candidate_form_title_edit: 'उम्मीदवार संपादित करें',
            label_candidate_name: 'उम्मीदवार का नाम',
            ph_candidate_name: 'उदा. आरव शर्मा',
            label_candidate_desc: 'पार्टी / विवरण',
            ph_candidate_desc: 'उदा. डिजिटल इंडिया पार्टी',
            btn_save_candidate: 'उम्मीदवार सहेजें',
            btn_cancel: 'रद्द करें',

            // Election Form (manage/election_form.html)
            election_form_title_create: 'नया चुनाव बनाएं',
            election_form_title_edit: 'चुनाव संपादित करें',
            label_election_title: 'चुनाव का शीर्षक',
            ph_election_title: 'उदा. 2026 राष्ट्रीय चुनाव',
            label_election_desc: 'विवरण',
            ph_election_desc: 'इस चुनाव के बारे में विवरण प्रदान करें...',
            label_start_time: 'प्रारंभ समय (UTC)',
            label_end_time: 'समाप्ति समय (UTC)',
            btn_save_election: 'चुनाव सहेजें',

            // Delete Confirmations (manage/confirm_delete)
            delete_election_title: 'चुनाव विलोपन की पुष्टि करें',
            delete_election_warning: 'क्या आप वाकई इस चुनाव को हटाना चाहते हैं:',
            delete_candidate_title: 'उम्मीदवार विलोपन की पुष्टि करें',
            delete_candidate_warning: 'क्या आप वाकई इस उम्मीदवार को हटाना चाहते हैं:',
            btn_confirm_delete_election: 'चुनाव हटाएं',
            btn_confirm_delete_candidate: 'उम्मीदवार हटाएं',
            btn_cancel_return: 'रद्द करें और वापस जाएं'
        }
    };

    // ── 2. DYNAMIC CONTENT LOCALIZATION DICTIONARY ────────────────────────
    // Maps approved canonical database strings to their official Hindi representations.
    // Important policy:
    // - Does not modify the underlying database or canonical records.
    // - Does not alter personal names (Aarav Sharma, Priya Verma, Rohan Mehta).
    // - User-created or unmapped content (e.g. 'TEST') cleanly falls back to canonical English.
    const dynamicTranslations = {
        // Election Titles
        "2026 National Election": "2026 राष्ट्रीय चुनाव",
        "Lok Sabha General Election 2029 (Demo)": "लोकसभा सामान्य चुनाव 2029 (डेमो)",
        "Best Programming Language 2025": "सर्वश्रेष्ठ प्रोग्रामिंग भाषा 2025",
        "ChainVote Network Audit & Protocol Ledger": "चेनवोट नेटवर्क ऑडिट एवं प्रोटोकॉल लेज़र",

        // Election Descriptions
        "National Digital Democracy Election powered by cryptographic ledgers.": "क्रिप्टोग्राफिक लेज़र द्वारा संचालित राष्ट्रीय डिजिटल लोकतंत्र चुनाव।",
        "National Digital Democracy Election powered by cryptographic ledgers": "क्रिप्टोग्राफिक लेज़र द्वारा संचालित राष्ट्रीय डिजिटल लोकतंत्र चुनाव",
        "Vote for your favorite programming language of the year.": "वर्ष की अपनी पसंदीदा प्रोग्रामिंग भाषा के लिए वोट करें।",
        "Official democratic elections for the 19th Lok Sabha representation.": "19वीं लोकसभा प्रतिनिधित्व के लिए आधिकारिक लोकतांत्रिक चुनाव।",
        "System protocol ledger tracking network-wide audit blocks.": "सिस्टम प्रोटोकॉल लेज़र जो नेटवर्क-व्यापी ऑडिट ब्लॉकों को ट्रैक करता है।",
        "No description provided": "कोई विवरण उपलब्ध नहीं है",

        // Political Parties & Candidate Affiliations / Descriptions
        "Digital India Party": "डिजिटल इंडिया पार्टी",
        "National Reform Alliance": "नेशनल रिफॉर्म अलायंस",
        "People's Development Front": "पीपल्स डेवलपमेंट फ्रंट",
        "Independent": "निर्दलीय",
        "Democratic Coalition": "डेमोक्रेटिक कोएलिशन",
        "Simple, readable, powerful.": "सरल, पठनीय और शक्तिशाली।",
        "The language of the web.": "वेब की सबसे लोकप्रिय भाषा।",
        "Fast, safe, and low-level.": "तेज़, सुरक्षित और सिस्टम-स्तरीय।",
        "Simple concurrency built-in.": "अंतर्निहित समवर्तीता (कॉनकरेंसी)।"
    };

    // ── 3. DATE & TIME TRANSLATION HELPERS ─────────────────────────────────
    function translateTimeuntil(str, lang) {
        if (lang !== 'hi' || !str) return str;
        return str
            .replace(/(\d+)\s*years?/gi, (m, d) => d === '1' ? '1 वर्ष' : d + ' वर्ष')
            .replace(/(\d+)\s*months?/gi, (m, d) => d === '1' ? '1 महीना' : d + ' महीने')
            .replace(/(\d+)\s*weeks?/gi, (m, d) => d === '1' ? '1 सप्ताह' : d + ' सप्ताह')
            .replace(/(\d+)\s*days?/gi, (m, d) => d === '1' ? '1 दिन' : d + ' दिन')
            .replace(/(\d+)\s*hours?/gi, (m, d) => d === '1' ? '1 घंटा' : d + ' घंटे')
            .replace(/(\d+)\s*minutes?/gi, (m, d) => d === '1' ? '1 मिनट' : d + ' मिनट')
            .replace(/,\s*/g, ', ');
    }

    function translateDate(str, lang) {
        if (lang !== 'hi' || !str) return str;
        const months = {
            'Jan': 'जनवरी', 'January': 'जनवरी',
            'Feb': 'फ़रवरी', 'February': 'फ़रवरी',
            'Mar': 'मार्च', 'March': 'मार्च',
            'Apr': 'अप्रैल', 'April': 'अप्रैल',
            'May': 'मई',
            'Jun': 'जून', 'June': 'जून',
            'Jul': 'जुलाई', 'July': 'जुलाई',
            'Aug': 'अगस्त', 'August': 'अगस्त',
            'Sep': 'सितंबर', 'September': 'सितंबर',
            'Oct': 'अक्टूबर', 'October': 'अक्टूबर',
            'Nov': 'नवंबर', 'November': 'नवंबर',
            'Dec': 'दिसंबर', 'December': 'दिसंबर'
        };
        let result = str;
        for (const [enMonth, hiMonth] of Object.entries(months)) {
            result = result.replace(new RegExp('\\b' + enMonth + '\\b', 'g'), hiMonth);
        }
        return result;
    }

    // ── 4. CORE LOCALIZATION ENGINE ───────────────────────────────────────
    function setLanguage(lang) {
        const targetLang = (lang === 'hi') ? 'hi' : 'en';

        // 1. Persist in localStorage and SameSite cookie
        try {
            localStorage.setItem('preferred-lang', targetLang);
        } catch (e) {
            console.warn('Unable to persist language in localStorage', e);
        }
        document.cookie = "preferred_lang=" + targetLang + "; path=/; max-age=31536000; SameSite=Lax";

        // 2. Update root HTML element
        document.documentElement.lang = targetLang;
        if (targetLang === 'hi') {
            document.documentElement.classList.add('lang-hi');
            document.body && document.body.classList.add('lang-hi');
        } else {
            document.documentElement.classList.remove('lang-hi');
            document.body && document.body.classList.remove('lang-hi');
        }

        const dict = translations[targetLang] || translations.en;

        // 3. Static UI strings ([data-i18n])
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (dict[key] !== undefined) {
                // If the key contains HTML formatting (like <br>), use innerHTML, else textContent
                if (dict[key].indexOf('<') !== -1) {
                    el.innerHTML = dict[key];
                } else {
                    el.textContent = dict[key];
                }
            }
        });

        // 4. Input placeholders ([data-i18n-placeholder])
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (dict[key] !== undefined) {
                el.placeholder = dict[key];
            }
        });

        // 5. Titles & tooltips ([data-i18n-title])
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            if (dict[key] !== undefined) {
                el.title = dict[key];
            }
        });

        // 6. Dynamic database-backed content ([data-i18n-dynamic])
        document.querySelectorAll('[data-i18n-dynamic]').forEach(el => {
            // Save canonical English value in data-en on first encounter
            if (!el.hasAttribute('data-en')) {
                el.setAttribute('data-en', el.textContent.trim());
            }
            const enText = el.getAttribute('data-en');
            if (targetLang === 'hi') {
                if (dynamicTranslations[enText]) {
                    el.textContent = dynamicTranslations[enText];
                } else {
                    // Fallback policy: display canonical name/title unchanged
                    el.textContent = enText;
                }
            } else {
                el.textContent = enText;
            }
        });

        // 7. Relative countdown text
        document.querySelectorAll('.countdown-text').forEach(el => {
            if (!el.hasAttribute('data-timeuntil-en')) {
                el.setAttribute('data-timeuntil-en', el.textContent.trim());
            }
            const enText = el.getAttribute('data-timeuntil-en');
            el.textContent = translateTimeuntil(enText, targetLang);
        });

        // 8. Absolute dates
        document.querySelectorAll('.date-text').forEach(el => {
            if (!el.hasAttribute('data-date-en')) {
                el.setAttribute('data-date-en', el.textContent.trim());
            }
            const enText = el.getAttribute('data-date-en');
            el.textContent = translateDate(enText, targetLang);
        });

        // 8b. Block headers in ledger
        document.querySelectorAll('.block-title').forEach(el => {
            if (targetLang === 'hi') {
                el.textContent = el.textContent.replace('Block #', 'ब्लॉक #');
            } else {
                el.textContent = el.textContent.replace('ब्लॉक #', 'Block #');
            }
        });

        // 9. Inline field error alerts (preserves real-time validation error state)
        document.querySelectorAll('[data-error-key]').forEach(el => {
            const errorKey = el.dataset.errorKey;
            if (dict[errorKey]) {
                el.textContent = dict[errorKey];
            }
        });
        const validationMsg = document.getElementById('validationAlertMsg');
        if (validationMsg && validationMsg.dataset.errorKey && dict[validationMsg.dataset.errorKey]) {
            validationMsg.textContent = dict[validationMsg.dataset.errorKey];
        }
        const aadhaarErrElem = document.getElementById('aadhaarError');
        const aadhaarErrText = document.getElementById('aadhaarErrorText');
        if (aadhaarErrElem && aadhaarErrElem.dataset.errorKey && aadhaarErrText && dict[aadhaarErrElem.dataset.errorKey]) {
            aadhaarErrText.textContent = dict[aadhaarErrElem.dataset.errorKey];
        }

        // 10. Language Toggle button text
        const langText = document.getElementById('lang-text');
        if (langText) {
            langText.textContent = dict.lang_btn;
        }

        // 11. Dispatch custom event for page-specific component hooks
        try {
            window.dispatchEvent(new CustomEvent('chainvote:languageChanged', {
                detail: { lang: targetLang, dict: dict }
            }));
        } catch (e) {
            // Older browser fallback
        }
    }

    function toggleLanguage() {
        const currentLang = localStorage.getItem('preferred-lang') || 'en';
        const nextLang = (currentLang === 'en') ? 'hi' : 'en';
        setLanguage(nextLang);
    }

    function i18nTranslate(key, fallback) {
        const currentLang = localStorage.getItem('preferred-lang') || 'en';
        const dict = translations[currentLang] || translations.en;
        return (dict && dict[key] !== undefined) ? dict[key] : (fallback || key);
    }

    function i18nTranslateDynamic(text) {
        const currentLang = localStorage.getItem('preferred-lang') || 'en';
        if (currentLang === 'hi' && dynamicTranslations[text]) {
            return dynamicTranslations[text];
        }
        return text;
    }

    // ── 5. EXPOSE TO GLOBAL SCOPE ─────────────────────────────────────────
    window.chainvoteTranslations = translations;
    window.chainvoteDynamicTranslations = dynamicTranslations;
    window.setLanguage = setLanguage;
    window.toggleLanguage = toggleLanguage;
    window.i18nTranslate = i18nTranslate;
    window.i18nTranslateDynamic = i18nTranslateDynamic;
    window.translateTimeuntil = translateTimeuntil;
    window.translateDate = translateDate;

    // ── 6. INITIALIZATION ON DOM READY ────────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            const savedLang = localStorage.getItem('preferred-lang') || 'en';
            setLanguage(savedLang);
        });
    } else {
        const savedLang = localStorage.getItem('preferred-lang') || 'en';
        setLanguage(savedLang);
    }

})();
