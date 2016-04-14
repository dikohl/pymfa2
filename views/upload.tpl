<script src="http://code.jquery.com/jquery-1.10.1.min.js"></script>
% rebase('layout.tpl', title=title)

<div class="jumbotron">
    <h1>PYMFA2.1</h1>
    <p class="lead">Choose a name for the output file and select a source .csv file.</p>
</div>

<div id="uploadForm">
	<form action="/upload" method="post" enctype="multipart/form-data" onSubmit="return loadingAnimation()">
		<table border="0">
			<tr>
				<p style="color:red;">{{ error }}&nbsp;</p>
			</tr>
			<tr>
				<td>
					<label>Name of output file:</label>
				</td>
				<td style="padding-left:30px;">
					<label>Select a source file:</label>
				</td>
				<td>
				</td>
			</tr>
			<tr>
				<td>
					<input type="text" name="outputFile"/>
				</td>
				<td style="padding-left:30px;">
					<input type="file" name="uploadFile"/>
				</td>
				<td>
        			<input id="start" type="submit" value="Start simulation" />
				</td>
			</tr>
		</table>
    </form>

	<div style="margin-top:30px;">
		<label>Previous results:</label>
		<table border="0">
		%for output, date in outputs.items():
			<tr>
				<td>
					{{ output }} </br>
					<div class="date">{{ date }}</div>
				</td>
				<td>
					<form action="/download" method="post" enctype="multipart/form-data">	
						<input type="text" name="output" value={{ output }} style="display:none;"/>
						<input type="text" name="date" value={{ date }} style="display:none;"/>
						<input type="submit" value="Download">
		  			</form>
				</td>
				<td style="padding:10px;">
					<form action="/download" method="post" enctype="multipart/form-data">	
						<input type="text" name="output" value='source' style="display:none;"/>
						<input type="text" name="date" value={{ date }} style="display:none;"/>
						<input type="submit" value="Source">
		  			</form>
				</td>
				<td>
					<form onsubmit="return handleDelete(this)" action="/delete" method="post" enctype="multipart/form-data">
						<input type="text" name="output" value={{ output }} style="display:none;"/>
						<input type="text" name="date" value={{ date }} style="display:none;"/>
						<input type="submit" value="Delete">
					</form>
				</td>
			</tr>
		%end
		</table>
	</div>
</div>

<div class='container' id="loading" style="display:none;">
  <div class='loader'>
    <div class='loader--dot'></div>
    <div class='loader--dot'></div>
    <div class='loader--dot'></div>
    <div class='loader--dot'></div>
    <div class='loader--dot'></div>
    <div class='loader--dot'></div>
    <div class='loader--text'></div>
  </div>
</div>

<footer style="margin-top:40px;">
    <form action="/logout" method="post" enctype="multipart/form-data">
       	<input type="submit" value="Logout"/>
   	</form>
</footer>

<script>
function loadingAnimation() {
    $( "#uploadForm" ).toggle();
	$( "#loading" ).toggle();
}

function handleDelete(formData){
	var d = window.confirm("You are deleting the file: \"" + formData.output.value + "\" are you sure?");
	if (d == true){
		return true
	} else {
		return false;
	}
}
</script>
