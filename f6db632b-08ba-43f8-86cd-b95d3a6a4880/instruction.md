# Implement `manifoldco/promptui`

You are given a Go repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that panics on call.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `manifoldco/promptui`
- Source directory to implement: `./`
- Test command: `go test -json -count=1 ./...` (run against `.`)
- Specification / docs: https://pkg.go.dev/github.com/manifoldco/promptui

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

Details Learn more about best practices Repository github.com/manifoldco/promptui Links Open Source Insights Code Wiki README ¶ Expand ▾ Documentation Overview Package promptui is a library providing a simple interface to create command-line prompts for go.

It can be easily integrated into spf13/cobra, urfave/cli or any cli go application.

Valid go.mod file Redistributable license Tagged version Stable version promptui Interactive prompt for command-line applications.

We built Promptui because we wanted to make it easy and fun to explore cloud services with manifold cli.

Code of Conduct | Contribution Guidelines latest latest v0.9.0 v0.9.0 godoc godoc reference reference 404 404 badge not found badge not found go report go report retired retired license license BSD BSD Overview promptui Interactive prompt for command-line applications.

We built Promptui because we wanted to make it easy and fun to explore cloud services with manifold cli.

Code of Conduct | Contribution Guidelines latest latest v0.9.0 v0.9.0 godoc godoc reference reference 404 404 badge not found badge not found go report go report retired retired license license BSD BSD Overview linux/amd64 README Discover Packages > github.com/manifoldco/promptui promptui package module Version: v0.9.0 Latest | Published: Oct 30, 2021 | License: BSD-3-Clause | Imports: 12 | Imported by: 3,547 go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

Okay promptui has two main input modes: Prompt provides a single line for user input. It supports optional live validation, confirmation and masking the input.

Select provides a list of options to choose from. It supports pagination, search, detailed view and custom templates.

Example (Prompt) Example (Select) Index Constants Variables func Styler(attrs ...attribute) func(interface{}) string type Cursor func NewCursor(startinginput string, pointer Pointer, eraseDefault bool) Cursor func (c *Cursor) Backspace() func (c *Cursor) End() func (c *Cursor) Format() string func (c *Cursor) FormatMask(mask rune) string func (c *Cursor) Get() string func (c *Cursor) GetMask(mask rune) string func (c *Cursor) Listen(line []rune, pos int, key rune) ([]rune, int, bool) func (c *Cursor) Move(shift int) func (c *Cursor) Place(position int) func (c *Cursor) Replace(input string) func (c *Cursor) Start() func (c *Cursor) String() string func (c *Cursor) Update(newinput string) type Key type Pointer type Prompt func (p *Prompt) Run() (string, error) type PromptTemplates type Select func (s *Select) Run() (int, string, error) func (s *Select) RunCursorAt(cursorPos, scroll int) (int, string, error) func (s *Select) ScrollPosition() int type SelectKeys type SelectTemplates type SelectWithAdd func (sa *SelectWithAdd) Run() (int, string, error) type ValidateFunc go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

Examples Package (Prompt) Package (Select) Prompt Select SelectWithAdd Constants View Source const ( FGBold attribute FGFaint FGItalic FGUnderline ) The possible state of text inside the application, either Bold, faint, italic or underline.

These constants are called through the use of the Styler function.

View Source const ( FGBlack attribute = iota + 30 FGRed FGGreen FGYellow FGBlue FGMagenta FGCyan FGWhite ) The possible colors of text inside the application.

These constants are called through the use of the Styler function.

View Source const ( BGBlack attribute = iota + 40 BGRed BGGreen BGYellow BGBlue BGMagenta BGCyan BGWhite ) The possible background colors of text inside the application.

go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

These constants are called through the use of the Styler function.

View Source const SelectedAdd = -1 SelectedAdd is used internally inside SelectWithAdd when the add option is selected in select mode.

Since -1 is not a possible selected index, this ensure that add mode is always unique inside SelectWithAdd's logic.

Variables View Source var ( // KeyEnter is the default key for submission/selection.

KeyEnter rune = readline.CharEnter // KeyCtrlH is the key for deleting input text.

KeyCtrlH rune = readline.CharCtrlH // KeyPrev is the default key to go up during selection.

KeyPrev rune = readline.CharPrev KeyPrevDisplay = "↑" // KeyNext is the default key to go down during selection.

KeyNext rune = readline.CharNext KeyNextDisplay = "↓" // KeyBackward is the default key to page up during selection.

KeyBackward rune = readline.CharBackward KeyBackwardDisplay = "←" // KeyForward is the default key to page down during selection.

KeyForward rune = readline.CharForward KeyForwardDisplay = "→" ) These runes are used to identify the commands entered by the user in the command prompt. They map to specific actions of promptui in prompt mode and can be remapped if necessary.

View Source var ( // IconInitial is the icon used when starting in prompt mode and the icon next to th // starting in select mode.

IconInitial = Styler(FGBlue)("?") // IconGood is the icon used when a good answer is entered in prompt mode.

IconGood = Styler(FGGreen)("✔") // IconWarn is the icon used when a good, but potentially invalid answer is entered IconWarn = Styler(FGYellow)("⚠") go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

// IconBad is the icon used when a bad answer is entered in prompt mode.

IconBad = Styler(FGRed)("✗") // IconSelect is the icon used to identify the currently selected item in select mod IconSelect = Styler(FGBold)("▸") ) These are the default icons used by promptui for select and prompts. These should not be overridden and instead customized through the use of custom templates View Source var ErrAbort = errors.New("") ErrAbort is the error returned when confirm prompts are supplied "n" View Source var ErrEOF = errors.New("^D") ErrEOF is the error returned from prompts when EOF is encountered.

View Source var ErrInterrupt = errors.New("^C") ErrInterrupt is the error returned from prompts when an interrupt (ctrl-c) is encountered.

View Source var FuncMap = template.FuncMap{ "black": Styler(FGBlack), "red": Styler(FGRed), "green": Styler(FGGreen), "yellow": Styler(FGYellow), "blue": Styler(FGBlue), "magenta": Styler(FGMagenta), "cyan": Styler(FGCyan), "white": Styler(FGWhite), "bgBlack": Styler(BGBlack), "bgRed": Styler(BGRed), "bgGreen": Styler(BGGreen), "bgYellow": Styler(BGYellow), "bgBlue": Styler(BGBlue), "bgMagenta": Styler(BGMagenta), "bgCyan": Styler(BGCyan), "bgWhite": Styler(BGWhite), "bold": Styler(FGBold), "faint": Styler(FGFaint), "italic": Styler(FGItalic), "underline": Styler(FGUnderline), } FuncMap defines template helpers for the output. It can be extended as a regular map.

go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

The functions inside the map link the state, color and background colors strings detected in templates to a Styler function that applies the given style using the corresponding constant.

View Source var ( // KeyBackspace is the default key for deleting input text.

KeyBackspace rune = readline.CharBackspace ) View Source var ResetCode = fmt.Sprintf("%s%dm", esc, reset) ResetCode is the character code used to reset the terminal formatting View Source var SearchPrompt = "Search: " SearchPrompt is the prompt displayed in search mode.

func Styler func Styler(attrs ...attribute) func(interface{}) string Styler is a function that accepts multiple possible styling transforms from the state, color and background colors constants and transforms them into a templated string to apply those styles in the CLI.

The returned styling function accepts a string that will be extended with the wrapping function's styling attributes.

Types type Cursor added in v0.4.0 type Cursor struct { // shows where the user inserts/updates text Cursor Pointer // Put the cursor before this slice Position int // contains filtered or unexported fields } Cursor tracks the state associated with the movable cursor The strategy is to keep the prompt, input pristine except for requested modifications. The insertion of the cursor happens during a `format` call and we read in new input via an `Update` call go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

func NewCursor added in v0.4.0 func NewCursor(startinginput string, pointer Pointer, eraseDefault bool) Cursor NewCursor create a new cursor, with the DefaultCursor, the specified input, and position at the end of the specified starting input.

func (*Cursor) Backspace added in v0.4.0 func (c *Cursor) Backspace() Backspace removes the rune that precedes the cursor It handles being at the beginning or end of the row, and moves the cursor to the appropriate position.

func (*Cursor) End added in v0.4.0 func (c *Cursor) End() End is a convenience for c.Place(len(c.input)) so you don't have to know how I indexed.

func (*Cursor) Format added in v0.4.0 func (c *Cursor) Format() string Format renders the input with the Cursor appropriately positioned.

func (*Cursor) FormatMask added in v0.4.0 func (c *Cursor) FormatMask(mask rune) string FormatMask replaces all input runes with the mask rune.

func (*Cursor) Get added in v0.4.0 func (c *Cursor) Get() string Get returns a copy of the input func (*Cursor) GetMask added in v0.8.0 func (c *Cursor) GetMask(mask rune) string GetMask returns a mask string with length equal to the input func (*Cursor) Listen added in v0.4.0 go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.
