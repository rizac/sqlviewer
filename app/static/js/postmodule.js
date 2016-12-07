angular.module('myApp', [])
.controller('myCtrl', function ($scope, $http) {
    $scope.dbAddress = "";
    $scope.tables = {};
    $scope.schemas = {};
    $scope.selectedSchemaName = "";
    $scope.selectedTable = undefined;
//    $scope.selectedTableName = "";
//    $scope.selectedStartRow = 0;
//    $scope.selectedTableData = [];
//    $scope.selectedTableColumns = [];
//    $scope.selectedTableColumnTypes = [];
//    $scope.foreignKeys = [];
//    $scope.primaryKey = {};
//    $scope.orderColName = null;
//    $scope.orderAscending = false;
    $scope.errorMsg = null;

    $scope.queryDb = function() {
    	$scope.schemas = {};
    	$scope.setSelectedSchemaName("");
    	var data = {
        	url: $scope.dbAddress
        };
        $http.post("/query_db", JSON.stringify(data),
        		{headers: {'Content-Type': 'application/json'}}
        ).then(function(response) {
        	data = response.data;
        	//url might be different than the supplied one if we are init (see set_cache_address
        	// in core.sql)
        	$scope.dbAddress = data.dburl;
        	var schemas = data.schemas;
        	for(var j=0; j<schemas.length; j++){
        		var schemaName = schemas[j][0];
        		var tablesAndInst = schemas[j][1];
        		var tables = {};
        		for(var i=0; i<tablesAndInst.length; i++){
        			tables[tablesAndInst[i][0]] = tablesAndInst[i][1];
        		}
        		$scope.schemas[schemaName] = tables;
        	}
            if(schemas.length==1){
            	$scope.setSelectedSchemaName(schemas[0][0]);
            }
        }, function(response) {
            // error handler
        	$scope.handleError(response);
        });
    }
    $scope.getNumTables = function(schemaName){
    	var tables = $scope.schemas[schemaName];
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
    $scope.setSelectedTableName = function(tableName){
    	$scope.selectedTable = undefined;
//    	$scope.selectedStartRow = 0;
//    	$scope.selectedTableName = table;
//    	$scope.selectedTableData = [];
//    	$scope.selectedTableColumns = [];
//        $scope.selectedTableColumnTypes = [];
//        $scope.foreignKeys = [];
//        $scope.primaryKey = {};
//    	$scope.orderColName = "";
    	$scope.queryTable(tableName);
    }
    $scope.queryTable = function(tableName) {
    	if (!tableName){
    		return;
    	}
        var data = {
        	schema_name: $scope.selectedSchemaName,
            table_name: tableName,
        	start_row: 0,
        	num_results: 20,
        	order_colname: $scope.selectedTable ? $scope.selectedTable.orderColName : null,
        	order_ascending: $scope.selectedTable ? $scope.selectedTable.orderAscending : true
        };
        $http.post("/query_table", JSON.stringify(data),
        		{headers: {'Content-Type': 'application/json'}}
        ).then(function(response) { // success handler
        	data = response.data;
        	$scope.selectedTable={ 	name: tableName,
        							data: data.data,
        							columns: data.columns,
        							types: data.types,
        							foreignKeys: data.fk || [],
        							primaryKey: data.pk || {},
        							uniqueConstraints: data.uc || [],
        							indexes: data.idx || []
        	};
        	var h = 9;
        }, function(response) {  // error handler
        	$scope.handleError(response);
        });
    }
    $scope.toggleColSort = function(colname){
    	var selT = $scope.selectedTable;
    	if (!selT){
    		return;
    	}
    	if (colname != selT.orderColName){
    		selT.orderAscending = false;  // will be set to true below
    	}
    	selT.orderColName = colname;
    	selT.orderAscending = !$scope.orderAscending;
    	$scope.queryTable(selT.name);
    }
    $scope.clearErrorMsg = function(){
    	$scope.errorMsg = null;
    }
    $scope.handleError = function(error){
    	$scope.errorMsg = "";
    	if (!error){
    		return;
    	}
    	if (error.status){
    		$scope.errorMsg = "[" + error.status + "] ";
    	}
    	if (error.data){
    		$scope.errorMsg += (error.data.message || error.data) + "";
    	}else{
    		$scope.errorMsg += error + "";
    	}
    }
    // see http://docs.sqlalchemy.org/en/latest/core/reflection.html
    $scope.getForeignKeyIndex = function(colName){
    	var fks = $scope.selectedTable ? $scope.selectedTable.foreignKeys : [];
    	for (var i=0; i<fks.length; i++){
    		if (fks[i].constrained_columns.indexOf(colName)>-1){
    			return i;
    		}
    	}
    	return -1;
    }
    $scope.isPrimaryKey = function(colName){
    	var pk = $scope.selectedTable ? $scope.selectedTable.primaryKey.constrained_columns : [];
    	return pk.indexOf(colName) > -1;
    }
    $scope.getuniqueConstraintsIndex = function(colName){
    	var ucs = $scope.selectedTable ? $scope.selectedTable.uniqueConstraints : [];
    	for (var i=0; i<ucs.length; i++){
    		if (ucs[i].column_names.indexOf(colName)>-1){
    			return i;
    		}
    	}
    	return -1;
    }
    $scope.queryDb();  // see if we passed the db url in the command line
})
