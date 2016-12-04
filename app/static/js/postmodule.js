angular.module('myApp', [])
.controller('myCtrl', function ($scope, $http) {
    $scope.dbAddress = "";
    $scope.tables = {};
    $scope.schemas = {};
    $scope.selectedSchemaName = "";
    $scope.selectedTableName = "";
    $scope.selectedStartRow = 0;
    $scope.selectedTableData = [];
    $scope.selectedTableDataHeader = [];
    $scope.orderColName = null;
    $scope.orderAscending = false;

    $scope.queryDb = function() {
        var data = {
        	url: $scope.dbAddress
        };
        $http.post("/query_db", JSON.stringify(data),
        		{headers: {'Content-Type': 'application/json'}}).success(function(data, status) {
        	$scope.schemas = {};
        	$scope.setSelectedSchemaName("");
        	for(var j=0; j<data.length; j++){
        		var schemaName = data[j][0];
        		var tablesAndInst = data[j][1];
        		var tables = {};
        		for(var i=0; i<tablesAndInst.length; i++){
        			tables[tablesAndInst[i][0]] = tablesAndInst[i][1];
        		}
        		$scope.schemas[schemaName] = tables;
        	}
            if(data.length==1){
            	$scope.setSelectedSchemaName(data[0][0]);
            }
        });
    }
    $scope.getNumTables = function(schemaName){
    	var tables = $scope[schemaName];
    	if(tables){
    		return Object.keys(tables).length;
    	}
    	return 0;
    }
    $scope.setSelectedSchemaName = function(schema){
    	$scope.selectedSchemaName = schema;
    	$scope.tables = $scope.schemas[schema] || {};
    	$scope.setSelectedTableName("");
    }
    $scope.setSelectedTableName = function(table){
    	$scope.selectedStartRow = 0;
    	$scope.selectedTableName = table;
    	$scope.selectedTableData = [];
    	$scope.selectedTableDataHeader = [];
    	$scope.orderColName = "";
    	$scope.queryTable();
    }
    $scope.queryTable = function() {
    	if (!$scope.selectedTableName){
    		return;
    	}
        var data = {
        	schema_name: $scope.selectedSchemaName,
            table_name: $scope.selectedTableName,
        	start_row: 0,
        	num_results: 20,
        	order_colname: $scope.orderColName,
        	order_ascending: $scope.orderAscending
        };
        $http.post("/query_table", JSON.stringify(data),
        		{headers: {'Content-Type': 'application/json'}}).success(function(data, status) {
        	$scope.selectedTableData = data.slice(2);
        	$scope.selectedTableDataHeader = data.slice(0, 2);
        });
    }
    $scope.toggleColSort = function(colname){
    	if (colname != $scope.orderColName){
    		$scope.orderAscending = false;  // will be set to true below
    	}
    	$scope.orderColName = colname;
    	$scope.orderAscending = !$scope.orderAscending;
    	$scope.queryTable();
    }
})
