```
█▀▀ █▀█ █░█ █▄░█ █▀▄ ▄▀█ ▀█▀ █ █▀█ █▄░█   █ █▀▀ █▀█ █▄░█ █▀
█▀░ █▄█ █▄█ █░▀█ █▄▀ █▀█ ░█░ █ █▄█ █░▀█   █ █▄▄ █▄█ █░▀█ ▄█
```

This is a package containing a version of Foundation Icon Fonts 3 icons.
Foundation Icons needed an npm module. So I took it upon my self to create this one.
That way it can be installed as an npm dependency instead of using a cdn or committing it to a project.

All credit goes to Zurb.I just needed this to be in npm moudule form for my projects. 

[The icons were downloaded from here](https://zurb.com/playground/foundation-icon-fonts-3)

## Usage
```
npm install foundation-icons
```

add this to your html, or import it with webpack
```
<link rel="stylesheet" href="./node_modules/foundation-icons/foundation-icons.css" />
```



## (Optional) Install Webpack loader

```
npm install url-loader
npm install file-loader
```

Configure The WebPack Loaders

```javascript
module.exports = {
  module: {
    loaders: [
      // the url-loader uses DataUrls.
      // the file-loader emits files.
      {
        test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader:
          'url-loader?limit=10000&mimetype=application/font-woff',
      },
      {
        test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'file-loader',
      },
    ],
  },
}
```
