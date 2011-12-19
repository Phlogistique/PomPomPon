require 'pp'

positions = [
  [0.15, 0.8],
  [0.20, 0.4],
  [0.5, 0.1],
  [0.80, 0.4],
  [0.85, 0.8]]

# :'<,'>rubyd $_.sub!(/\[.+?\]/){|i|s = "0000"; i.scan(/\d+/).map(&:to_i).each{|j|s[j]="1"}; "[\"#{s}\"]"}
matchings = {
  "0000" => :lol,
  "1100" => [0,2],
  "0110" => [1,2],
  "0011" => [2,3],
  "1001" => [2,4],
  "1010" => [0,3],
  "0101" => [2,4],
  "1110" => [0,1],
  "0111" => [3,4],
  "1011" => [1,4],
  "1101" => [0,4],
  "1000" => [0],
  "0100" => [1],
  "0010" => [3],
  "0001" => [4],
}

$f = []

def fexist n
  return true if File.exists? n
  return true if $f.include? n
  return false
end

def name diffi
  f = ""
  f << ARGF.filename
  f.sub!(/\..+?$/,"")
  f << diffi.to_s
  fpy = nil
  loop do
    fpy = f + ".py"
    break unless fexist fpy
    f << "_"
  end

  $f << fpy
  return fpy
end

contents = ARGF.read

def get_float(contents, r)
  res = contents.scan(r).flatten.first
  if not res
    $stderr.puts "Can't match #{r}"
    exit 1
  end
  res = res.to_f
end

bpm = get_float(contents, /^#BPMS:[^=]*=(\d+(?:\.\d*));/)
offset = get_float(contents, /^#OFFSET:(\d+(?:\.\d*));/)
signature = get_float(contents, /^#TIMESIGNATURES:[^=\n]*=(\d+)=\1\s*;/m).to_i

pp( {:BPM => bpm, :offset => offset, :signature => signature} )

notes = contents.scan(/^#NOTES:.+?\n[ \t]*(\d+):.*?\n(\d.+?);/m)

notes.reject!{|t|t[1] =~ /^\d{5}/}

notes.each do |level_times|
  level, defs = level_times
  fname = name level
  f = File.new fname, "w"

  time = offset
  
  mesures = defs.split(",").map{|t| t.strip.split(/[\r\n]+/).reject{|i| i =~ %r(^//)}}
  #f.puts "from song import Note, Touch, Hold"
  f.puts "["

  first = true
  mesures.each do |mesure|
    tlen = (60 / bpm) * signature / mesure.length * 2
    mesure.each do |temps|
      temps.strip!
      temps.gsub!(/2/, "1")  # no hold
      temps.gsub!(/3/, "0") 
      temps.gsub!(/m/i, "0")  # no mines
      next if temps == "0000"

      eq = matchings[temps.strip]
      if not eq
        $stderr.puts "#{temps.strip} untranslatable!"
        exit 1
      end

      eq.each do |touch|
        f.puts "#{first ? "" : ","} Touch(#{(time*1000).to_i}, (#{positions[touch][0]},#{positions[touch][1]}))"
        first = false
      end

      time += tlen
    end
  end

  f.puts "]"
  f.close

end

