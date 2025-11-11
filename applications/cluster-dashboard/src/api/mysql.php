<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

$action = $_GET['action'] ?? $_POST['action'] ?? 'databases';

// MySQL connection
function getConnection() {
    $host = 'cluster-mysql';
    $port = 3306;
    $username = 'root';
    $password = 'cluster_root_pass';
    $database = 'cluster_db';
    
    try {
        $pdo = new PDO("mysql:host=$host;port=$port;dbname=$database", $username, $password);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        return $pdo;
    } catch (PDOException $e) {
        throw new Exception("Connection failed: " . $e->getMessage());
    }
}

switch ($action) {
    case 'databases':
        echo json_encode(getDatabases());
        break;
    case 'tables':
        echo json_encode(getTables());
        break;
    case 'table_data':
        echo json_encode(getTableData());
        break;
    case 'table_structure':
        echo json_encode(getTableStructure());
        break;
    case 'execute_sql':
        echo json_encode(executeSQL());
        break;
    case 'create_database':
        echo json_encode(createDatabase());
        break;
    case 'create_table':
        echo json_encode(createTable());
        break;
    case 'insert_row':
        echo json_encode(insertRow());
        break;
    case 'update_row':
        echo json_encode(updateRow());
        break;
    case 'delete_row':
        echo json_encode(deleteRow());
        break;
    case 'drop_table':
        echo json_encode(dropTable());
        break;
    case 'drop_database':
        echo json_encode(dropDatabase());
        break;
    default:
        echo json_encode(['error' => 'Invalid action']);
}

function getDatabases() {
    try {
        $pdo = getConnection();
        $stmt = $pdo->query("SHOW DATABASES");
        $databases = [];
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            $db_name = $row['Database'];
            if (!in_array($db_name, ['information_schema', 'performance_schema', 'mysql', 'sys'])) {
                $databases[] = $db_name;
            }
        }
        return ['success' => true, 'databases' => $databases];
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function getTables() {
    $database = $_GET['database'] ?? '';
    if (!$database) {
        return ['success' => false, 'error' => 'Database name required'];
    }
    
    try {
        $pdo = getConnection();
        $pdo->exec("USE `$database`");
        $stmt = $pdo->query("SHOW TABLE STATUS");
        $tables = [];
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            $tables[] = [
                'name' => $row['Name'],
                'rows' => $row['Rows'] ?? 0,
                'size' => formatBytes($row['Data_length'] + $row['Index_length'])
            ];
        }
        return ['success' => true, 'tables' => $tables];
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function getTableData() {
    $database = $_GET['database'] ?? '';
    $table = $_GET['table'] ?? '';
    $limit = $_GET['limit'] ?? 100;
    $offset = $_GET['offset'] ?? 0;
    
    if (!$database || !$table) {
        return ['success' => false, 'error' => 'Database and table name required'];
    }
    
    try {
        $pdo = getConnection();
        $pdo->exec("USE `$database`");
        
        // Get column info
        $stmt = $pdo->query("DESCRIBE `$table`");
        $columns = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Get data
        $stmt = $pdo->query("SELECT * FROM `$table` LIMIT $limit OFFSET $offset");
        $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Get total count
        $stmt = $pdo->query("SELECT COUNT(*) as total FROM `$table`");
        $total = $stmt->fetch(PDO::FETCH_ASSOC)['total'];
        
        return [
            'success' => true,
            'columns' => $columns,
            'data' => $data,
            'total' => $total,
            'limit' => $limit,
            'offset' => $offset
        ];
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function getTableStructure() {
    $database = $_GET['database'] ?? '';
    $table = $_GET['table'] ?? '';
    
    if (!$database || !$table) {
        return ['success' => false, 'error' => 'Database and table name required'];
    }
    
    try {
        $pdo = getConnection();
        $pdo->exec("USE `$database`");
        
        $stmt = $pdo->query("DESCRIBE `$table`");
        $structure = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        return ['success' => true, 'structure' => $structure];
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function executeSQL() {
    $input = json_decode(file_get_contents('php://input'), true);
    $sql = $input['sql'] ?? '';
    
    if (!$sql) {
        return ['success' => false, 'error' => 'SQL query required'];
    }
    
    try {
        $pdo = getConnection();
        $stmt = $pdo->prepare($sql);
        $stmt->execute();
        
        if ($stmt->columnCount() > 0) {
            $result = $stmt->fetchAll(PDO::FETCH_ASSOC);
            return ['success' => true, 'result' => $result, 'type' => 'select'];
        } else {
            return ['success' => true, 'affected_rows' => $stmt->rowCount(), 'type' => 'modify'];
        }
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function createDatabase() {
    $input = json_decode(file_get_contents('php://input'), true);
    $name = $input['name'] ?? '';
    
    if (!$name) {
        return ['success' => false, 'error' => 'Database name required'];
    }
    
    try {
        $pdo = getConnection();
        $pdo->exec("CREATE DATABASE `$name`");
        return ['success' => true, 'message' => "Database '$name' created"];
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function createTable() {
    $input = json_decode(file_get_contents('php://input'), true);
    $database = $input['database'] ?? '';
    $table = $input['table'] ?? '';
    $columns = $input['columns'] ?? [];
    
    if (!$database || !$table || empty($columns)) {
        return ['success' => false, 'error' => 'Database, table name and columns required'];
    }
    
    try {
        $pdo = getConnection();
        $pdo->exec("USE `$database`");
        
        $columnDefs = [];
        foreach ($columns as $col) {
            $def = "`{$col['name']}` {$col['type']}";
            if ($col['null'] === false) $def .= ' NOT NULL';
            if (!empty($col['default'])) $def .= " DEFAULT '{$col['default']}'";
            if ($col['auto_increment']) $def .= ' AUTO_INCREMENT';
            $columnDefs[] = $def;
        }
        
        $sql = "CREATE TABLE `$table` (" . implode(', ', $columnDefs) . ")";
        $pdo->exec($sql);
        
        return ['success' => true, 'message' => "Table '$table' created"];
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function insertRow() {
    $input = json_decode(file_get_contents('php://input'), true);
    $database = $input['database'] ?? '';
    $table = $input['table'] ?? '';
    $data = $input['data'] ?? [];
    
    if (!$database || !$table || empty($data)) {
        return ['success' => false, 'error' => 'Database, table and data required'];
    }
    
    try {
        $pdo = getConnection();
        $pdo->exec("USE `$database`");
        
        $columns = array_keys($data);
        $placeholders = array_fill(0, count($columns), '?');
        
        $sql = "INSERT INTO `$table` (`" . implode('`, `', $columns) . "`) VALUES (" . implode(', ', $placeholders) . ")";
        $stmt = $pdo->prepare($sql);
        $stmt->execute(array_values($data));
        
        return ['success' => true, 'message' => 'Row inserted', 'id' => $pdo->lastInsertId()];
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function updateRow() {
    $input = json_decode(file_get_contents('php://input'), true);
    $database = $input['database'] ?? '';
    $table = $input['table'] ?? '';
    $data = $input['data'] ?? [];
    $where = $input['where'] ?? [];
    
    if (!$database || !$table || empty($data) || empty($where)) {
        return ['success' => false, 'error' => 'Database, table, data and where condition required'];
    }
    
    try {
        $pdo = getConnection();
        $pdo->exec("USE `$database`");
        
        $setParts = [];
        $values = [];
        foreach ($data as $col => $val) {
            $setParts[] = "`$col` = ?";
            $values[] = $val;
        }
        
        $whereParts = [];
        foreach ($where as $col => $val) {
            $whereParts[] = "`$col` = ?";
            $values[] = $val;
        }
        
        $sql = "UPDATE `$table` SET " . implode(', ', $setParts) . " WHERE " . implode(' AND ', $whereParts);
        $stmt = $pdo->prepare($sql);
        $stmt->execute($values);
        
        return ['success' => true, 'message' => 'Row updated', 'affected_rows' => $stmt->rowCount()];
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function deleteRow() {
    $input = json_decode(file_get_contents('php://input'), true);
    $database = $input['database'] ?? '';
    $table = $input['table'] ?? '';
    $where = $input['where'] ?? [];
    
    if (!$database || !$table || empty($where)) {
        return ['success' => false, 'error' => 'Database, table and where condition required'];
    }
    
    try {
        $pdo = getConnection();
        $pdo->exec("USE `$database`");
        
        $whereParts = [];
        $values = [];
        foreach ($where as $col => $val) {
            $whereParts[] = "`$col` = ?";
            $values[] = $val;
        }
        
        $sql = "DELETE FROM `$table` WHERE " . implode(' AND ', $whereParts);
        $stmt = $pdo->prepare($sql);
        $stmt->execute($values);
        
        return ['success' => true, 'message' => 'Row deleted', 'affected_rows' => $stmt->rowCount()];
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function dropTable() {
    $input = json_decode(file_get_contents('php://input'), true);
    $database = $input['database'] ?? '';
    $table = $input['table'] ?? '';
    
    if (!$database || !$table) {
        return ['success' => false, 'error' => 'Database and table name required'];
    }
    
    try {
        $pdo = getConnection();
        $pdo->exec("USE `$database`");
        $pdo->exec("DROP TABLE `$table`");
        
        return ['success' => true, 'message' => "Table '$table' dropped"];
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function dropDatabase() {
    $input = json_decode(file_get_contents('php://input'), true);
    $name = $input['name'] ?? '';
    
    if (!$name) {
        return ['success' => false, 'error' => 'Database name required'];
    }
    
    try {
        $pdo = getConnection();
        $pdo->exec("DROP DATABASE `$name`");
        
        return ['success' => true, 'message' => "Database '$name' dropped"];
    } catch (Exception $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function formatBytes($bytes) {
    if ($bytes >= 1073741824) {
        return number_format($bytes / 1073741824, 2) . ' GB';
    } elseif ($bytes >= 1048576) {
        return number_format($bytes / 1048576, 2) . ' MB';
    } elseif ($bytes >= 1024) {
        return number_format($bytes / 1024, 2) . ' KB';
    } else {
        return $bytes . ' bytes';
    }
}
?>