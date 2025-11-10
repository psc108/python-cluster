<?php
header('Content-Type: application/json');

$action = $_GET['action'] ?? $_POST['action'] ?? 'none';

echo json_encode([
    'received_action' => $action,
    'get_params' => $_GET,
    'post_params' => $_POST,
    'raw_input' => file_get_contents('php://input')
]);
?>