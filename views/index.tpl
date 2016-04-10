% rebase('layout.tpl', title=title)

<div class="jumbotron">
    <h1>PYMFA2.1</h1>
    <p class="lead">Please log in to use the tool.</p>
</div>

<div>
	<p style="color:red;">{{ error }}&nbsp;</p>
    <form action="/" method="post">
		<div class="login">
    		<label>Username:</label><br/>
			<input name="username" type="text" autofocus/>
		</div>
		<div class="login" style="margin-left:20px;">
			<label>Password:</label><br/>
			<input name="password" type="password"/>
			<input style="margin-left:20px;" value="Login" type="submit"/>
		</div>
        <div calss="login">
			
		</div>
	</from>
</div>
