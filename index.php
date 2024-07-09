<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TigerCZ</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    

    
    <main>
<h1>Alts</h1>
<h1>For search, press Ctrl + F</h1>


<?php
// Function to read lines from the text file
function read_lines_from_file($filename) {
    $lines = file($filename, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    return $lines;
}

// Read lines from the text file
$filename = 'blizzard_accounts.txt';
$lines = read_lines_from_file($filename);

// Initialize variables for tracking account change
$currentAccountID = null;

// Display data in tables, separating accounts
foreach ($lines as $line) {
    // Split the line into fields
    $fields = explode(',', $line);
    $account_id = trim($fields[1]);
    $character_name = trim($fields[2]);
    $realm = trim($fields[3]);

    // Check if we need to start a new table for a different account
    if ($account_id != $currentAccountID) {
        // Close previous table if it's not the first iteration
        if ($currentAccountID !== null) {
            echo "</table><br>";
        }

        // Start a new table for the current account
        echo "<table class='account-table'>";
        echo "<tr><th colspan='2'>Account ID: " . htmlspecialchars($account_id) . "</th></tr>";
        echo "<tr><th class='character-name-header'>Character Name</th><th class='realm-header'>Realm</th></tr>";

        // Update current account ID
        $currentAccountID = $account_id;
    }

    // Display character information
    echo "<tr>";
    echo "<td class='character-name-cell'>" . htmlspecialchars($character_name) . "</td>";
    echo "<td class='realm-cell'>" . htmlspecialchars($realm) . "</td>";
    echo "</tr>";
}

// Close the last table
echo "</table>";
?>

        
        
        
    </main>
    
    
</body>
</html>
