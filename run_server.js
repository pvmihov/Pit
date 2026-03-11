import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import archiver from 'archiver';
import unzipper from 'unzipper';


let root_dir = process.argv[2]
try
{
  const stats = await fs.stat(root_dir)
  if (!stats.isDirectory())
  {
    console.log('Path isn\'t a directory.')
    process.exit(0)
  }
}
catch (err)
{
  console.log('Couldn\'t open.')
  process.exit(0)
}
root_dir = path.resolve(root_dir)
console.log(`Using ${root_dir} as path.`)
let number = process.argv[3]
number = parseInt(number)
if (isNaN(number) || number<1024 || number>65535)
{
  console.log('Please enter a number in the range 1024 and 65535:\n')
  process.exit(0) 
}
async function create_pit(root_dir)
{
  console.log('.pit folder does not exist, so I am creating one.')
  await fs.mkdir(path.join(root_dir,'.pit'));
  await fs.mkdir(path.join(root_dir,'.pit','objects'))
  await fs.mkdir(path.join(root_dir,'.pit','refs','heads'),{recursive:true})
  await fs.writeFile(path.join(root_dir,'.pit','refs','heads','Main'),'-')
}
try
{
  let pit_dir = await fs.stat( path.join(root_dir,'.pit') )
  if (!pit_dir.isDirectory())
  {
    create_pit(root_dir)
  }
  else
  {
    console.log('.pit folder is found, so defaulting project to it.')
  }
}
catch (err)
{
  create_pit(root_dir)
}

console.log(`Using localhost:${number} as server.(Press Ctr-C to close)`)

http
  .createServer(async (request, response) => {
    if (request.method === 'GET' && request.url === '/clone')
    {
        response.writeHead(200, {
            'Content-Type': 'application/zip',
            'Content-Disposition': 'attachment; filename="project.zip"'
        })
        const archive = archiver('zip', {
            zlib: { level: 9 }
        })
        archive.on('error', (err) => {
            console.error("Archive error:", err)
            if (!response.headersSent) {
                response.writeHead(500)
            }
            response.end('Failed to generate archive')
        })
        archive.pipe(response)
        archive.directory(path.join(root_dir,'.pit'), '.pit');
        archive.finalize()
    }
    else if (request.method === 'GET' && request.url === '/fetch')
    {
        response.writeHead(200, {
            'Content-Type': 'application/zip',
            'Content-Disposition': 'attachment; filename="project.zip"'
        })
        const archive = archiver('zip', {
            zlib: { level: 9 }
        })
        archive.on('error', (err) => {
            console.error("Archive error:", err)
            if (!response.headersSent) {
                response.writeHead(500)
            }
            response.end('Failed to generate archive')
        })
        archive.pipe(response)
        archive.directory(path.join(root_dir,'.pit', 'objects'), 'objects');
        archive.finalize()
    }
    else if (request.method === 'GET' && request.url === '/branch')
    {
      let cur_branch = request.headers['x-current-branch']
      try {
        const data = await fs.readFile(path.join(root_dir, '.pit', 'refs', 'heads', cur_branch), { encoding: 'utf8' })
        const data_text = data.toString()
        response.writeHead(200,{
          'Content-Type': 'text/plain'
        })
        response.write(data_text)
        response.end()
      } catch (err) {
        if (err.code === 'ENOENT')
        {
          response.statusCode = 204
          response.end()
        }
      }
      response.end()
    }
    else if (request.method === 'POST' && request.url === '/push')
    {
      ///currently the push is kinda unsafe, as it allows files to rewrite what was there
      const extractStream = unzipper.Extract({ path: path.join(root_dir, '.pit') })
      extractStream.on('close', async () => {
            let cur_branch = request.headers['x-current-branch']
            let cur_commit = request.headers['x-new-last-commit']
            await fs.writeFile(path.join(root_dir,'.pit','refs','heads',cur_branch),cur_commit)
            response.status = 200
            response.end()
      })
      extractStream.on('error', (err) => {
            console.error("Stream extraction failed:", err);
            response.status = 500
            response.end()
      })
      request.on('error', (err) => {
            console.error("Stream extraction failed:", err);
            response.status = 500
            response.end()
      })
      request.pipe(extractStream);
    }
    else
    {
      response.statusCode = 404
      response.end()
    }
  })
  .listen(number);

